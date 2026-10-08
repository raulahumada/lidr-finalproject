from app.domain.answer_service import AnswerService
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
