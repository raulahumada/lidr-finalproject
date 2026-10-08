"""Semantic retriever: embed query → cosine rank → SearchResponse."""

from __future__ import annotations

import time
from typing import Optional

from sqlalchemy.orm import sessionmaker

from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.embedder import OpenAIEmbedder
from app.schemas.search import SearchHit, SearchResponse


class SemanticRetriever:
    def __init__(
        self,
        embedder: OpenAIEmbedder,
        session_factory: sessionmaker,
        store: Optional[ChunkStore] = None,
    ) -> None:
        self._embedder = embedder
        self._session_factory = session_factory
        self._store = store or ChunkStore()

    def search(self, *, query: str, k: int) -> SearchResponse:
        started = time.perf_counter()
        query_vector = self._embedder.embed_one(query)

        with self._session_factory() as session:
            rows = self._store.search_by_embedding(session, query_vector=query_vector, k=k)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return SearchResponse(
            query=query,
            k=k,
            search_time_ms=elapsed_ms,
            results=[
                SearchHit(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    chunk_type=row.chunk_type,
                    content=row.content,
                    score=max(0.0, 1.0 - row.distance),
                    distance=row.distance,
                    source_path=row.source_path,
                    document_type=row.document_type,
                    metadata=row.metadata,
                )
                for row in rows
            ],
        )
