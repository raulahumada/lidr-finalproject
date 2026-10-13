from __future__ import annotations

import time
from typing import Any

from fastapi.testclient import TestClient

from app.config import get_settings
from app.domain.graph.activity import GraphActivityLog
from app.domain.graph.checkpointer import reset_checkpointer
from app.domain.graph.runner import AgenticAnswerRunner
from app.main import create_app
from app.schemas.search import SearchHit, SearchResponse


class FakeRetriever:
    def __init__(self, results: list[SearchHit] | None = None) -> None:
        self.results = results or []

    def search(self, *, query: str, k: int) -> SearchResponse:
        return SearchResponse(query=query, k=k, search_time_ms=1, results=self.results)


class FakeChat:
    model = "gpt-test"

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        return {"answer": "ok progress", "citation_indices": [0]}


def _hit() -> SearchHit:
    return SearchHit(
        chunk_id=1,
        document_id=10,
        chunk_type="recursive",
        content="Tenela handoff.",
        score=0.95,
        distance=0.05,
        source_path="docs/tenela.md",
        document_type="md",
        metadata={},
    )


def _wait_terminal(client: TestClient, thread_id: str, *, timeout_s: float = 5.0) -> dict:
    deadline = time.time() + timeout_s
    last: dict = {}
    while time.time() < deadline:
        res = client.get(f"/api/v1/answer/agentic/{thread_id}/progress")
        assert res.status_code == 200
        last = res.json()
        if last["status"] != "running":
            return last
        time.sleep(0.05)
    raise AssertionError(f"still running after {timeout_s}s: {last}")


def test_start_and_progress_completed(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()
    reset_checkpointer()

    from app import dependencies

    dependencies.get_activity_log.cache_clear()
    activity = GraphActivityLog()
    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
        settings=get_settings(),
        activity_log=activity,
    )

    app = create_app()
    app.dependency_overrides[dependencies.get_agentic_answer_runner] = lambda: runner
    app.dependency_overrides[dependencies.get_activity_log] = lambda: activity
    client = TestClient(app)

    start = client.post(
        "/api/v1/answer/agentic/start",
        json={"question": "¿Qué es Tenela?"},
    )
    assert start.status_code == 202
    body = start.json()
    assert body["status"] == "running"
    thread_id = body["thread_id"]
    assert thread_id

    final = _wait_terminal(client, thread_id)
    assert final["status"] == "completed"
    assert final["answer"]
    assert final["activity"]
    assert any(e["node"] == "intent_framer" for e in final["activity"])


def test_progress_404_unknown_thread(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()

    from app import dependencies

    dependencies.get_activity_log.cache_clear()
    app = create_app()
    app.dependency_overrides[dependencies.get_activity_log] = lambda: GraphActivityLog()
    client = TestClient(app)

    res = client.get("/api/v1/answer/agentic/does-not-exist/progress")
    assert res.status_code == 404


def test_start_503_without_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    get_settings.cache_clear()
    from app import dependencies

    dependencies.get_chunk_store.cache_clear()
    client = TestClient(create_app())
    res = client.post("/api/v1/answer/agentic/start", json={"question": "hola"})
    assert res.status_code == 503


def test_start_pauses_for_human_review(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.99")
    get_settings.cache_clear()
    reset_checkpointer()

    from app import dependencies

    dependencies.get_activity_log.cache_clear()
    activity = GraphActivityLog()
    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
        settings=get_settings(),
        activity_log=activity,
    )
    app = create_app()
    app.dependency_overrides[dependencies.get_agentic_answer_runner] = lambda: runner
    app.dependency_overrides[dependencies.get_activity_log] = lambda: activity
    client = TestClient(app)

    start = client.post(
        "/api/v1/answer/agentic/start",
        json={"question": "cobranzas"},
    )
    assert start.status_code == 202
    final = _wait_terminal(client, start.json()["thread_id"])
    assert final["status"] == "awaiting_human_review"
    assert final["review_reasons"]
