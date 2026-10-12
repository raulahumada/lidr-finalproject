"""Composition root: wire singletons for API dependencies."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import redis
from openai import OpenAI

from app.config import Settings, get_settings
from app.domain.answer_service import AnswerService, build_knowledge_pack
from app.foundation.llm.chat import ChatClient
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.generation.cag.exact import ExactAnswerCache
from app.generation.cag.semantic import SemanticAnswerCache
from app.generation.rag.embedder import OpenAIEmbedder
from app.generation.rag.retriever import SemanticRetriever

log = logging.getLogger(__name__)


@lru_cache
def get_chunk_store() -> ChunkStore:
    return ChunkStore()


def get_semantic_retriever() -> Optional[SemanticRetriever]:
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


def _try_redis(url: str) -> redis.Redis | None:
    try:
        client = redis.from_url(url, decode_responses=True)
        client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        log.warning("redis_unavailable: %s", exc)
        return None


def get_answer_service() -> Optional[AnswerService]:
    settings = get_settings()
    if not settings.embeddings_configured:
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    embedder = OpenAIEmbedder(client=client, model=settings.embedding_model)
    retriever = SemanticRetriever(
        embedder=embedder,
        session_factory=get_session_factory(),
        store=get_chunk_store(),
    )
    chat = ChatClient(client, model=settings.chat_model)

    exact: ExactAnswerCache | None = None
    semantic: SemanticAnswerCache | None = None
    redis_client = _try_redis(settings.redis_url)
    if redis_client is not None:
        exact = ExactAnswerCache(redis_client, ttl=settings.answer_cache_ttl_seconds)
        try:
            # redisvl wants a client without decode_responses for vector bytes
            raw = redis.from_url(settings.redis_url, decode_responses=False)
            semantic = SemanticAnswerCache(
                redis_client=raw,
                embedder=embedder,
                threshold=settings.semantic_cache_threshold,
                ttl=settings.answer_cache_ttl_seconds,
                log_only=settings.semantic_cache_log_only,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("semantic_cache_init_failed: %s", exc)

    knowledge = build_knowledge_pack(settings.knowledge_pack_max_tokens)
    return AnswerService(
        retriever=retriever,
        chat=chat,
        exact_cache=exact,
        semantic_cache=semantic,
        knowledge_pack=knowledge,
        prompt_version=settings.answer_prompt_version,
        default_k=settings.answer_default_k,
        context_max_tokens=settings.answer_context_max_tokens,
    )
