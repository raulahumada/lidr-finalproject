"""Composition root: wire singletons for API dependencies."""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from app.config import Settings, get_settings
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.embedder import OpenAIEmbedder
from app.generation.rag.retriever import SemanticRetriever


@lru_cache
def get_chunk_store() -> ChunkStore:
    return ChunkStore()


def get_semantic_retriever():
    """Return a retriever when embeddings are configured; otherwise None → 503."""
    settings: Settings = get_settings()
    if not settings.embeddings_configured:
        return None
    client = OpenAI(api_key=settings.openai_api_key)
    embedder = OpenAIEmbedder(client=client, model=settings.embedding_model)
    return SemanticRetriever(
        embedder=embedder,
        session_factory=get_session_factory(),
        store=get_chunk_store(),
    )
