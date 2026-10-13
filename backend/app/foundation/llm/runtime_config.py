"""Runtime-mutable chat model overrides, backed by Redis.

``Settings.chat_model`` stays the immutable default. Overrides live in a Redis
hash so operators can hot-swap role models without editing ``.env`` or
restarting Uvicorn. Embedding model is intentionally not overridable here.
"""

from __future__ import annotations

import logging
from typing import Literal, Protocol

import redis

from app.config import Settings

log = logging.getLogger(__name__)

ChatRole = Literal["chat", "composer", "prompt_specialist"]

CHAT_ROLES: tuple[ChatRole, ...] = ("chat", "composer", "prompt_specialist")

HASH_KEY = "lidr:runtime_models"


class RuntimeConfigUnavailable(Exception):
    """Raised when an override WRITE fails (Redis unreachable)."""


class _RedisHash(Protocol):
    def hget(self, name: str, key: str) -> str | None: ...
    def hset(self, name: str, key: str, value: str) -> object: ...
    def hdel(self, name: str, *keys: str) -> object: ...
    def hgetall(self, name: str) -> dict[str, str]: ...


class RuntimeModelConfig:
    """Redis-hash-backed override store for Metropol chat roles."""

    def __init__(self, redis_client: _RedisHash | None, settings: Settings) -> None:
        self._redis = redis_client
        self._settings = settings

    def _validate_role(self, role: str) -> ChatRole:
        if role not in CHAT_ROLES:
            raise ValueError(f"Unknown chat role: {role}")
        return role  # type: ignore[return-value]

    def get(self, role: str) -> str | None:
        key = self._validate_role(role)
        if self._redis is None:
            return None
        try:
            value = self._redis.hget(HASH_KEY, key)
            if value is None:
                return None
            text = str(value).strip()
            return text or None
        except redis.RedisError as exc:
            log.warning("runtime_config_read_failed role=%s err=%s", key, exc)
            return None

    def set(self, role: str, value: str | None) -> None:
        key = self._validate_role(role)
        if self._redis is None:
            raise RuntimeConfigUnavailable("Redis is not available")
        try:
            if value is None:
                self._redis.hdel(HASH_KEY, key)
            else:
                self._redis.hset(HASH_KEY, key, value)
        except redis.RedisError as exc:
            raise RuntimeConfigUnavailable(str(exc)) from exc

    def default(self) -> str:
        return self._settings.chat_model

    def effective(self, role: str) -> str:
        """Role override → chat override → settings.chat_model."""
        key = self._validate_role(role)
        own = self.get(key)
        if own:
            return own
        if key != "chat":
            chat_override = self.get("chat")
            if chat_override:
                return chat_override
        return self.default()

    def is_overridden(self, role: str) -> bool:
        return self.get(role) is not None

    def snapshot(self) -> dict[str, dict[str, str | bool]]:
        return {
            role: {
                "effective": self.effective(role),
                "default": self.default(),
                "overridden": self.is_overridden(role),
            }
            for role in CHAT_ROLES
        }

    def apply_updates(self, models: dict[str, str | None]) -> None:
        for role, value in models.items():
            self._validate_role(role)
            if value is not None and not str(value).strip():
                value = None
            if value is not None:
                value = str(value).strip()
            self.set(role, value)


class InMemoryRedisHash:
    """Test double for RuntimeModelConfig (dict-backed)."""

    def __init__(self) -> None:
        self._data: dict[str, dict[str, str]] = {}

    def hget(self, name: str, key: str) -> str | None:
        return self._data.get(name, {}).get(key)

    def hset(self, name: str, key: str, value: str) -> int:
        self._data.setdefault(name, {})[key] = value
        return 1

    def hdel(self, name: str, *keys: str) -> int:
        bucket = self._data.get(name, {})
        removed = 0
        for key in keys:
            if key in bucket:
                del bucket[key]
                removed += 1
        return removed

    def hgetall(self, name: str) -> dict[str, str]:
        return dict(self._data.get(name, {}))
