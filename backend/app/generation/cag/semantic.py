"""Semantic response cache (Redis Stack + redisvl), course-aligned."""

from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import numpy as np

log = logging.getLogger(__name__)


class Embedder(Protocol):
    def embed_one(self, text: str) -> list[float]: ...


def _to_bytes(vector: list[float]) -> bytes:
    return np.array(vector, dtype=np.float32).tobytes()


_INDEX_SCHEMA: dict[str, Any] = {
    "index": {
        "name": "answers",
        "prefix": "answer:semantic",
        "storage_type": "hash",
    },
    "fields": [
        {"name": "bucket", "type": "tag"},
        {"name": "result_json", "type": "text"},
        {
            "name": "embedding",
            "type": "vector",
            "attrs": {
                "dims": 1536,
                "distance_metric": "cosine",
                "algorithm": "flat",
            },
        },
    ],
}


class SemanticAnswerCache:
    def __init__(
        self,
        *,
        redis_client: Any,
        embedder: Embedder,
        threshold: float = 0.92,
        ttl: int = 86400,
        log_only: bool = True,
        index_name: str = "answers",
    ) -> None:
        from redisvl.index import SearchIndex

        self.embedder = embedder
        self.threshold = threshold
        self.ttl = ttl
        self.log_only = log_only

        schema = dict(_INDEX_SCHEMA)
        schema["index"] = {**_INDEX_SCHEMA["index"], "name": index_name}
        self.index = SearchIndex.from_dict(schema)
        self.index.set_client(redis_client)
        try:
            self.index.create(overwrite=False)
        except Exception as exc:  # noqa: BLE001
            log.debug("semantic_index_create_skipped: %s", str(exc)[:120])

    @staticmethod
    def bucket_for(*, prompt_version: str, model: str, k: int) -> str:
        return f"{prompt_version}:{model}:{k}"

    def lookup(
        self,
        *,
        question: str,
        prompt_version: str,
        model: str,
        k: int,
    ) -> dict[str, Any] | None:
        try:
            from redisvl.query import VectorQuery
            from redisvl.query.filter import Tag
        except ImportError:
            return None

        bucket = self.bucket_for(prompt_version=prompt_version, model=model, k=k)
        try:
            embedding = self.embedder.embed_one(question)
            query = VectorQuery(
                vector=_to_bytes(embedding),
                vector_field_name="embedding",
                return_fields=["result_json", "bucket"],
                num_results=1,
                return_score=True,
                filter_expression=Tag("bucket") == bucket,
            )
            results = self.index.query(query)
        except Exception as exc:  # noqa: BLE001
            log.warning("semantic_cache_lookup_failed: %s", exc)
            return None

        if not results:
            return None

        hit = results[0]
        distance = float(hit.get("vector_distance", 1.0))
        similarity = 1.0 - distance
        log.info(
            "semantic_cache_lookup bucket=%s similarity=%.4f threshold=%.4f",
            bucket,
            similarity,
            self.threshold,
        )
        if similarity < self.threshold:
            return None
        if self.log_only:
            log.info("semantic_cache_hit_log_only similarity=%.4f", similarity)
            return None
        try:
            return json.loads(hit["result_json"])
        except (KeyError, json.JSONDecodeError):
            return None

    def store(
        self,
        *,
        question: str,
        prompt_version: str,
        model: str,
        k: int,
        payload: dict[str, Any],
    ) -> None:
        bucket = self.bucket_for(prompt_version=prompt_version, model=model, k=k)
        try:
            embedding = self.embedder.embed_one(question)
            self.index.load(
                [
                    {
                        "bucket": bucket,
                        "result_json": json.dumps(payload),
                        "embedding": _to_bytes(embedding),
                    }
                ],
                ttl=self.ttl,
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("semantic_cache_store_failed: %s", exc)
