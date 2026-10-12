"""Process-scoped MemorySaver for agentic interrupts (v1)."""

from __future__ import annotations

from langgraph.checkpoint.memory import MemorySaver

_checkpointer: MemorySaver | None = None


def get_checkpointer() -> MemorySaver:
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def reset_checkpointer() -> MemorySaver:
    """Replace the saver (tests / process recycle)."""
    global _checkpointer
    _checkpointer = MemorySaver()
    return _checkpointer
