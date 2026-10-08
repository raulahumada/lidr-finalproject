from __future__ import annotations

from typing import Any

from app.domain.answer_service import AnswerService
from app.schemas.answer import AnswerResponse
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

    def __init__(self) -> None:
        self.calls = 0

    def complete_json(self, *, system: str, user: str) -> dict[str, Any]:
        self.calls += 1
        assert "Metropol" in system or "pack" in system.lower() or "conocimiento" in system
        return {"answer": "Respuesta grounded.", "citation_indices": [0]}


class MemoryExact:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        return self.store.get(key)

    def set(self, key: str, response: dict[str, Any]) -> None:
        self.store[key] = response


def _hit() -> SearchHit:
    return SearchHit(
        chunk_id=1,
        document_id=10,
        chunk_type="recursive",
        content="Tenela integra agentes de cobranzas.",
        score=0.9,
        distance=0.1,
        source_path="docs/tenela.md",
        document_type="md",
        metadata={"strategy": "markdown"},
    )


def test_no_evidence_skips_llm() -> None:
    chat = FakeChat()
    service = AnswerService(
        retriever=FakeRetriever([]),  # type: ignore[arg-type]
        chat=chat,  # type: ignore[arg-type]
        exact_cache=None,
        semantic_cache=None,
        knowledge_pack="## Qué es este pack y qué NO es\npack",
        prompt_version="v1",
        default_k=3,
    )
    result = service.answer(question="algo inexistente")
    assert result.no_evidence is True
    assert result.citations == []
    assert chat.calls == 0
    assert "evidencia" in result.answer.lower() or "corpus" in result.answer.lower()


def test_generate_and_exact_cache_hit() -> None:
    chat = FakeChat()
    exact = MemoryExact()
    retriever = FakeRetriever([_hit()])
    service = AnswerService(
        retriever=retriever,  # type: ignore[arg-type]
        chat=chat,  # type: ignore[arg-type]
        exact_cache=exact,  # type: ignore[arg-type]
        semantic_cache=None,
        knowledge_pack="## Qué es este pack y qué NO es\npack Metropol",
        prompt_version="v1",
        default_k=3,
    )
    first = service.answer(question="¿Qué es Tenela?")
    assert first.cached == "false"
    assert first.citations[0].source_path == "docs/tenela.md"
    assert chat.calls == 1

    second = service.answer(question="¿Qué es Tenela?")
    assert second.cached == "exact"
    assert second.answer == first.answer
    assert chat.calls == 1
    assert retriever.calls == 1


def test_semantic_log_only_does_not_serve() -> None:
    class LogOnlySemantic:
        def lookup(self, **_: Any) -> dict[str, Any] | None:
            return None  # log_only path already returns None inside real cache

        def store(self, **_: Any) -> None:
            return None

    chat = FakeChat()
    service = AnswerService(
        retriever=FakeRetriever([_hit()]),  # type: ignore[arg-type]
        chat=chat,  # type: ignore[arg-type]
        exact_cache=None,
        semantic_cache=LogOnlySemantic(),  # type: ignore[arg-type]
        knowledge_pack="## Qué es este pack y qué NO es\npack",
        prompt_version="v1",
        default_k=3,
    )
    result = service.answer(question="Tenela")
    assert isinstance(result, AnswerResponse)
    assert result.cached == "false"
    assert chat.calls == 1
