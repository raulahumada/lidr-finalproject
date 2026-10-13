from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import create_app


def _postgres_available() -> bool:
    settings = get_settings()
    if not settings.database_url.strip():
        return False
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    # Session tests target ownership, not the service-token gate.
    monkeypatch.setenv("SERVICE_TOKEN", "")
    get_settings.cache_clear()
    return TestClient(create_app())


@pytest.mark.integration
def test_session_crud_roundtrip(client: TestClient) -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    created = client.post("/api/v1/answer/session")
    assert created.status_code == 201
    session_id = created.json()["session_id"]
    assert session_id

    listed = client.get("/api/v1/answer/sessions")
    assert listed.status_code == 200
    assert any(item["session_id"] == session_id for item in listed.json())

    got = client.get(f"/api/v1/answer/session/{session_id}")
    assert got.status_code == 200
    assert got.json()["history"] == []

    renamed = client.patch(
        f"/api/v1/answer/session/{session_id}",
        json={"title": "Handoff Tenela"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["title"] == "Handoff Tenela"

    deleted = client.delete(f"/api/v1/answer/session/{session_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/answer/session/{session_id}").status_code == 404


@pytest.mark.integration
def test_session_owner_header_isolation(client: TestClient) -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    headers_a = {"X-Console-User": "owner-a"}
    headers_b = {"X-Console-User": "owner-b"}

    created_a = client.post("/api/v1/answer/session", headers=headers_a)
    assert created_a.status_code == 201
    id_a = created_a.json()["session_id"]

    created_b = client.post("/api/v1/answer/session", headers=headers_b)
    assert created_b.status_code == 201
    id_b = created_b.json()["session_id"]

    listed_a = client.get("/api/v1/answer/sessions", headers=headers_a)
    assert listed_a.status_code == 200
    ids_a = {item["session_id"] for item in listed_a.json()}
    assert id_a in ids_a
    assert id_b not in ids_a

    assert (
        client.get(f"/api/v1/answer/session/{id_b}", headers=headers_a).status_code
        == 404
    )
    assert (
        client.delete(f"/api/v1/answer/session/{id_b}", headers=headers_a).status_code
        == 404
    )

    # No header → unowned bucket only (neither A nor B).
    listed_open = client.get("/api/v1/answer/sessions")
    assert listed_open.status_code == 200
    open_ids = {item["session_id"] for item in listed_open.json()}
    assert id_a not in open_ids
    assert id_b not in open_ids

    client.delete(f"/api/v1/answer/session/{id_a}", headers=headers_a)
    client.delete(f"/api/v1/answer/session/{id_b}", headers=headers_b)


@pytest.mark.integration
def test_agentic_unknown_session_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/answer/agentic",
        json={"question": "hola", "session_id": "does-not-exist"},
    )
    assert response.status_code == 404


@pytest.mark.integration
def test_agentic_foreign_session_404(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    client = TestClient(create_app())

    created = client.post(
        "/api/v1/answer/session",
        headers={"X-Console-User": "owner-a"},
    )
    assert created.status_code == 201
    session_id = created.json()["session_id"]

    response = client.post(
        "/api/v1/answer/agentic/start",
        headers={"X-Console-User": "owner-b"},
        json={"question": "hola", "session_id": session_id},
    )
    assert response.status_code == 404

    client.delete(
        f"/api/v1/answer/session/{session_id}",
        headers={"X-Console-User": "owner-a"},
    )
