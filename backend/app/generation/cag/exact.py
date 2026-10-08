"""Exact-match Redis cache for answer payloads."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

import redis

log = logging.getLogger(__name__)


class ExactAnswerCache:
    def __init__(self, redis_client: redis.Redis, ttl: int = 86400) -> None:
        self.redis = redis_client
        self.ttl = ttl

    @classmethod
    def from_url(cls, url: str, ttl: int = 86400) -> ExactAnswerCache:
        return cls(redis.from_url(url, decode_responses=True), ttl=ttl)

    @staticmethod
    def make_key(
        *,
        question: str,
        prompt_version: str,
        model: str,
        k: int,
    ) -> str:
        payload = json.dumps(
            {
                "question": question.strip(),
                "prompt_version": prompt_version,
                "model": model,
                "k": k,
            },
            sort_keys=True,
        )
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"answer:exact:{digest}"

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            cached = self.redis.get(key)
        except redis.RedisError as exc:
            log.warning("exact_cache_get_failed: %s", exc)
            return None
        if not cached:
            return None
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            log.warning("exact_cache_corrupt key=%s", key[:24])
            return None

    def set(self, key: str, response: dict[str, Any]) -> None:
        try:
            self.redis.setex(key, self.ttl, json.dumps(response))
        except redis.RedisError as exc:
            log.warning("exact_cache_set_failed: %s", exc)
