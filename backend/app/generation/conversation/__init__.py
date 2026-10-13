"""Conversation sessions + memory helpers for agentic turns.

Transcript durability lives in ``store``. Retrieval-first memory (resolver +
budgeted prompt block) lives beside it — same capability family as Cristian's
``conversation-memory``, Metropol naming.
"""

from app.generation.conversation.budget import MemoryBlock, render_memory
from app.generation.conversation.resolver import ResolvedQuestion, resolve
from app.generation.conversation.store import SessionNotFoundError, SessionStore

__all__ = [
    "MemoryBlock",
    "ResolvedQuestion",
    "SessionNotFoundError",
    "SessionStore",
    "render_memory",
    "resolve",
]
