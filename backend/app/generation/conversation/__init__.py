"""Conversation sessions + memory helpers for agentic turns.

Transcript durability lives in ``store``. Retrieval-first memory (resolver +
budgeted prompt block + facts/anchors) lives beside it — same capability
family as Cristian's ``conversation-memory``, Metropol naming.
"""

from app.generation.conversation.anchors import (
    acknowledge_scope_pin,
    detect_anchors,
    is_scope_pin_only,
    pinned_domain,
)
from app.generation.conversation.budget import MemoryBlock, render_memory
from app.generation.conversation.facts import facts_from_turn
from app.generation.conversation.models import (
    Anchor,
    ConversationFacts,
    SessionMemory,
    merge_anchors,
)
from app.generation.conversation.resolver import ResolvedQuestion, resolve
from app.generation.conversation.store import SessionNotFoundError, SessionStore

__all__ = [
    "Anchor",
    "ConversationFacts",
    "MemoryBlock",
    "ResolvedQuestion",
    "SessionMemory",
    "SessionNotFoundError",
    "SessionStore",
    "acknowledge_scope_pin",
    "detect_anchors",
    "facts_from_turn",
    "is_scope_pin_only",
    "merge_anchors",
    "pinned_domain",
    "render_memory",
    "resolve",
]
