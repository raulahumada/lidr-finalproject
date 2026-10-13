"""HTTP tests for /api/v1/ingest/*."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_chunk_store, get_ingest_job_registry
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.ingestion.jobs import IngestJobRegistry
from app.ingestion.orchestrator import IngestSummary
from app.main import app


def _settings(
    *,
    corpus_root: str = "",
    openai_api_key: str = "test-key",
    database_url: str | None = None,
) -> Settings:
    base = get_settings()
    return Settings(
        corpus_root=corpus_root,
        openai_api_key=openai_api_key,
        database_url=database_url if database_url is not None else base.database_url,
        corpus_extensions="txt,md",
    )


def test_start_without_corpus_root_returns_503() -> None:
    registry = IngestJobRegistry()
    app.dependency_overrides[get_settings] = lambda: _settings(corpus_root="")
    app.dependency_overrides[get_ingest_job_registry] = lambda: registry
    try:
        response = TestClient(app).post("/api/v1/ingest/runs", json={"force": False})
        assert response.status_code == 503
        assert "CORPUS_ROOT" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_start_poll_completed_with_fake_executor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import app.api.routes.ingest as ingest_routes

    (tmp_path / "note.txt").write_text("hola metropol", encoding="utf-8")
    registry = IngestJobRegistry()

    def fake_execute(**kwargs: object) -> None:
        run_id = str(kwargs["run_id"])
        reg = kwargs["registry"]
        assert isinstance(reg, IngestJobRegistry)
        reg.mark_running(run_id)
        reg.complete(
            run_id,
            IngestSummary(seen=1, ingested=1, chunks=2),
        )

    monkeypatch.setattr(ingest_routes, "_execute_ingest_run", fake_execute)
    app.dependency_overrides[get_settings] = lambda: _settings(corpus_root=str(tmp_path))
    app.dependency_overrides[get_ingest_job_registry] = lambda: registry
    try:
        client = TestClient(app)
        start = client.post("/api/v1/ingest/runs", json={"force": True})
        assert start.status_code == 202
        body = start.json()
        assert body["status"] == "queued"
        run_id = body["run_id"]
        poll = client.get(f"/api/v1/ingest/runs/{run_id}")
        assert poll.status_code == 200
        status_body = poll.json()
        assert status_body["status"] == "completed"
        assert status_body["force"] is True
        assert status_body["summary"]["ingested"] == 1
        assert status_body["summary"]["chunks"] == 2
    finally:
        app.dependency_overrides.clear()


def test_concurrent_run_returns_409(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    registry = IngestJobRegistry()
    registry.create(force=False)
    app.dependency_overrides[get_settings] = lambda: _settings(corpus_root=str(tmp_path))
    app.dependency_overrides[get_ingest_job_registry] = lambda: registry
    try:
        response = TestClient(app).post("/api/v1/ingest/runs", json={})
        assert response.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_unknown_run_returns_404() -> None:
    registry = IngestJobRegistry()
    app.dependency_overrides[get_ingest_job_registry] = lambda: registry
    try:
        response = TestClient(app).get("/api/v1/ingest/runs/does-not-exist")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_stats_returns_counts() -> None:
    store = ChunkStore()
    factory = get_session_factory()
    with factory() as session:
        before = store.count_corpus(session)
    app.dependency_overrides[get_chunk_store] = lambda: store
    app.dependency_overrides[get_settings] = lambda: _settings(
        corpus_root="/tmp/corpus-demo",
        openai_api_key="",
    )
    try:
        response = TestClient(app).get("/api/v1/ingest/stats")
        assert response.status_code == 200
        body = response.json()
        assert body["document_count"] == before.document_count
        assert body["chunk_count"] == before.chunk_count
        assert body["corpus_root"] == "/tmp/corpus-demo"
        assert "txt" in body["allowlist"]
    finally:
        app.dependency_overrides.clear()
