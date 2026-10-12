from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from app.config import get_settings
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
        return {"answer": "ok agentic", "citation_indices": [0]}


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


def test_agentic_503_without_openai_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from app import dependencies

    get_settings.cache_clear()
    dependencies.get_chunk_store.cache_clear()

    client = TestClient(create_app())
    response = client.post("/api/v1/answer/agentic", json={"question": "hola"})
    assert response.status_code == 503


def test_agentic_200_and_404_resume(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()
    reset_checkpointer()

    from app import dependencies

    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
        settings=get_settings(),
    )

    app = create_app()
    app.dependency_overrides[dependencies.get_agentic_answer_runner] = lambda: runner
    client = TestClient(app)

    response = client.post(
        "/api/v1/answer/agentic",
        json={"question": "¿Qué es Tenela?", "k": 3},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["agent_trace"]

    missing = client.post(
        "/api/v1/answer/agentic/does-not-exist/resume",
        json={"decision": "approve"},
    )
    assert missing.status_code == 404


def test_agentic_202_pause_and_resume(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()
    reset_checkpointer()

    from app import dependencies

    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
        settings=get_settings(),
    )
    app = create_app()
    app.dependency_overrides[dependencies.get_agentic_answer_runner] = lambda: runner
    client = TestClient(app)

    paused = client.post("/api/v1/answer/agentic", json={"question": "nada"})
    assert paused.status_code == 202
    thread_id = paused.json()["thread_id"]
    assert paused.json()["status"] == "awaiting_human_review"

    resumed = client.post(
        f"/api/v1/answer/agentic/{thread_id}/resume",
        json={"decision": "approve"},
    )
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "completed"


def test_agentic_202_on_low_confidence(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.95")
    get_settings.cache_clear()
    reset_checkpointer()

    from app import dependencies

    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
        settings=get_settings(),
    )
    app = create_app()
    app.dependency_overrides[dependencies.get_agentic_answer_runner] = lambda: runner
    client = TestClient(app)

    paused = client.post(
        "/api/v1/answer/agentic",
        json={"question": "¿Qué es Tenela?", "k": 3},
    )
    assert paused.status_code == 202
    body = paused.json()
    assert body["status"] == "awaiting_human_review"
    assert body["no_evidence"] is False
    assert any("confidence" in r for r in body["review_reasons"])

    resumed = client.post(
        f"/api/v1/answer/agentic/{body['thread_id']}/resume",
        json={"decision": "approve"},
    )
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "completed"
