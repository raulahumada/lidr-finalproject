from app.domain.answer_service import AnswerService
from app.domain.graph.agents.grounded_composer import grounded_composer
from app.domain.graph.agents.source_guard import source_guard
from app.domain.graph.gate import review_reasons
from app.domain.grounding import LONG_ANSWER_CHARS, NO_EVIDENCE_ANSWER
from app.foundation.prompts.loader import render_answer_prompts
from app.generation.rag.context_blocks import fit_to_budget
from tests.test_answer_service import FakeChat, FakeRetriever, _hit


def test_v2_system_has_partial_answer_policy() -> None:
    system, user = render_answer_prompts(
        version="v2",
        knowledge_pack="## Qué es este pack y qué NO es\npack",
        question="¿handoff?",
        context="### 1. [id=9]\nsource_path: x.md\n\ntexto",
    )
    assert "parcial" in system.lower() or "parte de la pregunta" in system.lower()
    assert "[id=9]" in user
    assert "¿handoff?" in user


def test_v2_system_forbids_invented_procedures() -> None:
    system, _user = render_answer_prompts(
        version="v2",
        knowledge_pack="pack",
        question="¿handoff?",
        context="### 1. [id=1]\nsource_path: x.md\n\ntexto",
    )
    lower = system.lower()
    assert "procedimiento" in lower
    assert "invent" in lower
    assert "abstenci" in lower or "evidencia fina" in lower


def test_fabricated_citation_filtered() -> None:
    chat = FakeChat()
    chat_result = {"answer": "ok", "citation_indices": [0, 99], "citation_ids": [1, 999]}

    class ScriptedChat(FakeChat):
        def complete_json(self, *, system: str, user: str):
            self.calls += 1
            assert "[id=1]" in user
            return chat_result

    service = AnswerService(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=ScriptedChat(),  # type: ignore[arg-type]
        exact_cache=None,
        semantic_cache=None,
        knowledge_pack="## Qué es este pack y qué NO es\npack Metropol",
        prompt_version="v2",
        default_k=3,
        context_max_tokens=3500,
    )
    result = service.answer(question="Tenela")
    assert [c.chunk_id for c in result.citations] == [1]
    assert result.prompt_version == "v2"


def test_citations_from_model_drops_unknown_chunk_id() -> None:
    hit = _hit()
    blocks = fit_to_budget([hit], max_tokens=3500)
    assert len(blocks) == 1
    citations = AnswerService._citations_from_model(
        blocks, {"citation_indices": [], "citation_ids": [999]}
    )
    assert citations == []


def test_grounded_composer_skips_llm_on_no_evidence() -> None:
    class BoomChat:
        def complete_json(self, *, system: str, user: str):
            raise AssertionError("LLM must not run on no_evidence")

    out = grounded_composer(
        {"no_evidence": True, "hits": [], "agent_trace": []},
        {"configurable": {"chat": BoomChat()}},
    )
    assert out["no_evidence"] is True
    assert out["answer"] == NO_EVIDENCE_ANSWER
    assert "procedimiento" in out["answer"].lower()
    assert "1." not in out["answer"] and "2." not in out["answer"]


def test_sync_answer_skips_llm_on_empty_retrieve() -> None:
    class BoomChat(FakeChat):
        def complete_json(self, *, system: str, user: str):
            raise AssertionError("LLM must not run without hits")

    service = AnswerService(
        retriever=FakeRetriever([]),  # type: ignore[arg-type]
        chat=BoomChat(),  # type: ignore[arg-type]
        exact_cache=None,
        semantic_cache=None,
        knowledge_pack="pack",
        prompt_version="v2",
        default_k=3,
    )
    result = service.answer(question="fuera de corpus")
    assert result.no_evidence is True
    assert result.answer == NO_EVIDENCE_ANSWER
    assert result.citations == []


def test_thin_grounding_lowers_confidence_and_review() -> None:
    long_answer = "x" * (LONG_ANSWER_CHARS + 10)
    guarded = source_guard(
        {
            "hits": [_hit().model_dump()],
            "citations": [
                {
                    "chunk_id": 1,
                    "document_id": 10,
                    "source_path": "a",
                    "document_type": "md",
                    "score": 0.9,
                    "excerpt": "x",
                    "metadata": {},
                }
            ],
            "answer": long_answer,
            "no_evidence": False,
            "confidence": 0.8,
            "agent_trace": [],
        }
    )
    assert guarded["confidence"] <= 0.45
    reasons = review_reasons(
        {
            "confidence": guarded["confidence"],
            "citations_valid": True,
            "no_evidence": False,
            "hits": [_hit().model_dump()],
            "answer": long_answer,
            "citations": guarded["citations"],
        }
    )
    assert any("few citations" in r for r in reasons)
