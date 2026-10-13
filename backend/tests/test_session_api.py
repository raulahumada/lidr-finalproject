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


@pytest.mark.integration
def test_session_crud_roundtrip() -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    client = TestClient(create_app())
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
def test_agentic_unknown_session_404(monkeypatch: pytest.MonkeyPatch) -> None:
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
