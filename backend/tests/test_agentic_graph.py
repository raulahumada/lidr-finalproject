from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.domain.graph.agents.intent_framer import intent_framer
from app.domain.graph.agents.source_guard import source_guard
from app.domain.graph.checkpointer import reset_checkpointer
from app.domain.graph.gate import review_reasons
from app.domain.graph.runner import AgenticAnswerRunner
from app.schemas.search import SearchHit, SearchResponse


class FakeRetriever:
    def __init__(self, results: list[SearchHit] | None = None) -> None:
        self.results = results or []
        self.calls = 0

    def search(self, *, query: str, k: int) -> SearchResponse:
        self.calls += 1
        return SearchResponse(query=query, k=k, search_time_ms=1, results=self.results)


class FakeChat:
    model = "gpt-test"

    def __init__(self, *, citation_indices: list[int] | None = None) -> None:
        self.calls = 0
        self.citation_indices = citation_indices if citation_indices is not None else [0]

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        self.calls += 1
        return {"answer": "Respuesta agentic grounded.", "citation_indices": self.citation_indices}


def _hit(chunk_id: int = 1) -> SearchHit:
    return SearchHit(
        chunk_id=chunk_id,
        document_id=10,
        chunk_type="recursive",
        content="Tenela integra agentes de cobranzas.",
        score=0.9,
        distance=0.1,
        source_path="docs/tenela.md",
        document_type="md",
        metadata={"strategy": "markdown"},
    )


def test_intent_framer_pass_through() -> None:
    out = intent_framer({"question": "  hola  ", "agent_trace": []})
    assert out["framed_query"] == "hola"
    assert out["agent_trace"][0]["node"] == "intent_framer"


def test_source_guard_drops_unknown_chunk() -> None:
    out = source_guard(
        {
            "hits": [_hit(1).model_dump()],
            "citations": [
                {"chunk_id": 1, "document_id": 10, "source_path": "a", "document_type": "md", "score": 0.9, "excerpt": "x", "metadata": {}},
                {"chunk_id": 999, "document_id": 10, "source_path": "a", "document_type": "md", "score": 0.9, "excerpt": "x", "metadata": {}},
            ],
            "confidence": 0.8,
            "agent_trace": [],
        }
    )
    assert len(out["citations"]) == 1
    assert out["citations_valid"] is False


def test_review_reasons_empty_on_good_state(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()
    reasons = review_reasons(
        {
            "confidence": 0.8,
            "citations_valid": True,
            "no_evidence": False,
            "hits": [_hit().model_dump()],
        }
    )
    assert reasons == []


def test_review_reasons_on_no_evidence(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()
    reasons = review_reasons(
        {
            "confidence": 0.0,
            "citations_valid": True,
            "no_evidence": True,
            "hits": [],
        }
    )
    assert any("no evidence" in r for r in reasons)


def test_review_reasons_on_low_confidence(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.55")
    get_settings.cache_clear()
    reasons = review_reasons(
        {
            "confidence": 0.40,
            "citations_valid": True,
            "no_evidence": False,
            "hits": [_hit().model_dump()],
        }
    )
    assert len(reasons) == 1
    assert "confidence" in reasons[0]
    assert "0.40" in reasons[0]


def test_runner_completes_with_evidence(monkeypatch) -> None:
    reset_checkpointer()
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: [],
    )
    retriever = FakeRetriever([_hit()])
    chat = FakeChat()
    runner = AgenticAnswerRunner(
        retriever=retriever,  # type: ignore[arg-type]
        chat=chat,  # type: ignore[arg-type]
    )
    result = runner.start(question="¿Qué es Tenela?", k=3)
    assert result.status == "completed"
    assert result.answer
    assert chat.calls == 1
    assert retriever.calls == 1
    assert result.domain == "tenela"
    assert result.routing_history
    assert result.custom_notes == []
    nodes = [s.node for s in result.agent_trace]
    assert "orchestrator" in nodes
    for required in (
        "intent_framer",
        "corpus_fetcher",
        "grounded_composer",
        "source_guard",
        "escalation_gate",
    ):
        assert required in nodes
    assert [r.next_agent for r in result.routing_history] == [
        "intent_framer",
        "corpus_fetcher",
        "grounded_composer",
        "source_guard",
        "finish",
    ]


def test_runner_pauses_without_evidence_then_resume() -> None:
    reset_checkpointer()
    get_settings.cache_clear()
    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
    )
    paused = runner.start(question="sin corpus")
    assert paused.status == "awaiting_human_review"
    assert paused.review_reasons
    done = runner.resume(thread_id=paused.thread_id, decision="approve")
    assert done.status == "completed"
    assert done.no_evidence is True


def test_runner_pauses_on_low_confidence(monkeypatch) -> None:
    """With evidence + valid citations, a high threshold still trips confidence."""
    monkeypatch.setenv("AGENTIC_CONFIDENCE_THRESHOLD", "0.95")
    get_settings.cache_clear()
    reset_checkpointer()
    runner = AgenticAnswerRunner(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=FakeChat(),  # type: ignore[arg-type]
        settings=get_settings(),
    )
    paused = runner.start(question="¿Qué es Tenela?", k=3)
    assert paused.status == "awaiting_human_review"
    assert paused.no_evidence is False
    assert any("confidence" in r for r in paused.review_reasons)
    assert paused.confidence is not None and paused.confidence < 0.95
    done = runner.resume(thread_id=paused.thread_id, decision="approve")
    assert done.status == "completed"
