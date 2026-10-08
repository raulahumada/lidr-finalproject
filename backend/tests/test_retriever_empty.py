"""Integration: semantic retriever returns [] on empty corpus (mocked embedder)."""

from __future__ import annotations

from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.constants import EMBEDDING_DIMENSIONS
from app.generation.rag.retriever import SemanticRetriever


class _FakeEmbedder:
    def embed_one(self, text: str) -> list[float]:
        return [0.0] * EMBEDDING_DIMENSIONS


def test_retriever_empty_corpus_returns_no_results() -> None:
    retriever = SemanticRetriever(
        embedder=_FakeEmbedder(),  # type: ignore[arg-type]
        session_factory=get_session_factory(),
        store=ChunkStore(),
    )
    response = retriever.search(query="cobranzas Metropol", k=5)
    assert response.query == "cobranzas Metropol"
    assert response.k == 5
    assert response.results == []
