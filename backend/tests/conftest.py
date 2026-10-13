"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from app.config import get_settings
from app.domain.graph.checkpointer import reset_checkpointer


@pytest.fixture(autouse=True)
def _default_memory_checkpointer(monkeypatch: pytest.MonkeyPatch):
    """Keep unit/API tests off Postgres (lifespan would otherwise open a pool)."""
    monkeypatch.setenv("AGENTIC_CHECKPOINTER", "memory")
    # Local .env may set SERVICE_TOKEN (locked mode); suite defaults to open mode.
    # Tests in test_service_token.py override explicitly.
    monkeypatch.setenv("SERVICE_TOKEN", "")
    get_settings.cache_clear()
    reset_checkpointer()
    yield
    reset_checkpointer()
    get_settings.cache_clear()
