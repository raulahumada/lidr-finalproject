"""Unit tests for RuntimeModelConfig (no real Redis)."""

from __future__ import annotations

import pytest

from app.config import Settings
from app.foundation.llm.runtime_config import (
    InMemoryRedisHash,
    RuntimeConfigUnavailable,
    RuntimeModelConfig,
)


def _settings(**kwargs: object) -> Settings:
    return Settings(chat_model="gpt-4o-mini", available_chat_models="gpt-4o-mini,gpt-4o", **kwargs)


def test_effective_defaults_and_cascade() -> None:
    store = InMemoryRedisHash()
    runtime = RuntimeModelConfig(store, _settings())
    assert runtime.effective("composer") == "gpt-4o-mini"
    runtime.set("chat", "gpt-4o")
    assert runtime.effective("composer") == "gpt-4o"
    assert runtime.effective("prompt_specialist") == "gpt-4o"
    runtime.set("composer", "gpt-4o-mini")
    assert runtime.effective("composer") == "gpt-4o-mini"
    assert runtime.effective("prompt_specialist") == "gpt-4o"


def test_clear_override() -> None:
    store = InMemoryRedisHash()
    runtime = RuntimeModelConfig(store, _settings())
    runtime.set("chat", "gpt-4o")
    runtime.set("chat", None)
    assert runtime.is_overridden("chat") is False
    assert runtime.effective("chat") == "gpt-4o-mini"


def test_write_without_redis_raises() -> None:
    runtime = RuntimeModelConfig(None, _settings())
    with pytest.raises(RuntimeConfigUnavailable):
        runtime.set("chat", "gpt-4o")
