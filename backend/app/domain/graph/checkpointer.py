"""LangGraph checkpointer: Postgres (durable) or MemorySaver (tests / offline)."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import Settings, get_settings

log = logging.getLogger(__name__)

_CONNECTION_KWARGS: dict[str, Any] = {
    "autocommit": True,
    "prepare_threshold": 0,
    "row_factory": dict_row,
}
_POOL_MIN_SIZE = 1
_POOL_MAX_SIZE = 10

_LANGGRAPH_CHECKPOINT_TABLES = frozenset(
    {
        "checkpoints",
        "checkpoint_writes",
        "checkpoint_blobs",
        "checkpoint_migrations",
    }
)

_checkpointer: MemorySaver | PostgresSaver | None = None
_pool: ConnectionPool | None = None


def saver_conninfo(settings: Settings | None = None) -> str:
    """Plain libpq DSN for PostgresSaver (strip SQLAlchemy driver tokens)."""
    url = (settings or get_settings()).database_url.strip()
    if "+psycopg" in url:
        return url.replace("+psycopg", "", 1)
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "", 1)
    return url


def uses_memory_checkpointer(settings: Settings | None = None) -> bool:
    """Whether the process should use in-process MemorySaver."""
    settings = settings or get_settings()
    mode = settings.agentic_checkpointer.strip().lower() or "auto"
    if mode == "memory":
        return True
    if mode == "postgres":
        return False
    # auto
    return not bool(settings.database_url.strip())


def is_langgraph_checkpoint_table(name: str | None) -> bool:
    """True for LangGraph-owned tables (exclude from Alembic autogenerate)."""
    return bool(name) and name in _LANGGRAPH_CHECKPOINT_TABLES


def get_checkpointer() -> MemorySaver | PostgresSaver:
    global _checkpointer
    if _checkpointer is None:
        if uses_memory_checkpointer():
            _checkpointer = MemorySaver()
        else:
            raise RuntimeError(
                "Postgres checkpointer is not open; app lifespan must call "
                "open_checkpointer() before agentic runs"
            )
    return _checkpointer


def open_checkpointer(settings: Settings | None = None) -> MemorySaver | PostgresSaver:
    """Open (or replace) the process checkpointer. Called from app lifespan."""
    global _checkpointer, _pool

    settings = settings or get_settings()
    close_checkpointer()

    if uses_memory_checkpointer(settings):
        _checkpointer = MemorySaver()
        log.info("agentic_checkpointer_ready mode=memory")
        return _checkpointer

    conninfo = saver_conninfo(settings)
    if not conninfo:
        raise RuntimeError("DATABASE_URL is required for Postgres checkpointer")

    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=_POOL_MIN_SIZE,
        max_size=_POOL_MAX_SIZE,
        kwargs=_CONNECTION_KWARGS,
        open=False,
    )
    pool.open(wait=True)
    try:
        saver = PostgresSaver(pool)
        saver.setup()
    except Exception:
        pool.close()
        raise

    _pool = pool
    _checkpointer = saver
    log.info("agentic_checkpointer_ready mode=postgres pool_max=%s", _POOL_MAX_SIZE)
    return saver


def close_checkpointer() -> None:
    """Close pool and drop the process singleton (shutdown / test recycle)."""
    global _checkpointer, _pool
    if _pool is not None:
        try:
            _pool.close()
        except Exception as exc:  # noqa: BLE001
            log.warning("checkpointer_pool_close_failed: %s", exc)
        _pool = None
    _checkpointer = None


def reset_checkpointer() -> MemorySaver:
    """Replace the saver with a fresh MemorySaver (tests / process recycle)."""
    global _checkpointer
    close_checkpointer()
    _checkpointer = MemorySaver()
    return _checkpointer
