"""Integration: paused agentic threads resume after checkpointer reopen (Postgres)."""

from __future__ import annotations

from typing import Any

import pytest

from app.config import get_settings
from app.domain.graph.checkpointer import (
    close_checkpointer,
    get_checkpointer,
    open_checkpointer,
    uses_memory_checkpointer,
)
from app.domain.graph.runner import AgenticAnswerRunner
from app.schemas.search import SearchHit, SearchResponse
from langgraph.checkpoint.postgres import PostgresSaver


class FakeRetriever:
    def search(self, *, query: str, k: int) -> SearchResponse:
        return SearchResponse(query=query, k=k, search_time_ms=1, results=[])


class FakeChat:
    model = "gpt-test"

    def complete_json(self, *, system: str, user: str, role: str = "chat") -> dict[str, Any]:
        return {"answer": "should pause", "citation_indices": [0]}


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
def test_pause_survives_checkpointer_reopen(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AGENTIC_CHECKPOINTER", "postgres")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()

    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    assert not uses_memory_checkpointer(get_settings())

    try:
        open_checkpointer()
        assert isinstance(get_checkpointer(), PostgresSaver)

        runner = AgenticAnswerRunner(
            retriever=FakeRetriever(),  # type: ignore[arg-type]
            chat=FakeChat(),  # type: ignore[arg-type]
            settings=get_settings(),
        )
        paused = runner.start(question="sin evidencia")
        assert paused.status == "awaiting_human_review"
        assert paused.thread_id
        thread_id = paused.thread_id

        # Simulate API process restart: close pool and open a fresh saver on the same DB.
        close_checkpointer()
        open_checkpointer()
        assert isinstance(get_checkpointer(), PostgresSaver)

        runner2 = AgenticAnswerRunner(
            retriever=FakeRetriever(),  # type: ignore[arg-type]
            chat=FakeChat(),  # type: ignore[arg-type]
            settings=get_settings(),
        )
        resumed = runner2.resume(thread_id=thread_id, decision="approve")
        assert resumed.status == "completed"
        assert resumed.thread_id == thread_id
    finally:
        close_checkpointer()
