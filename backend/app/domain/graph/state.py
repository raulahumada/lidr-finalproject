"""Shared state for the Metropol agentic answer graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgenticAnswerState(TypedDict, total=False):
    question: str
    k: int
    session_id: str
    domain: str
    conversation_window: list[dict[str, Any]]
    conversation_facts: dict[str, Any]
    conversation_anchors: list[dict[str, Any]]
    scope_pin_only: bool
    framed_query: str
    resolved_question: str
    resolved_substituted: list[str]
    hits: list[dict[str, Any]]
    answer: str
    citations: list[dict[str, Any]]
    citations_valid: bool
    no_evidence: bool
    confidence: float
    review_reasons: list[str]
    needs_human_review: bool
    status: str
    human_decision: dict[str, Any]
    prompt_version: str
    next_agent: str
    route_reason: str
    supervisor_steps: int
    custom_notes: Annotated[list[dict[str, Any]], operator.add]
    routing_history: Annotated[list[dict[str, Any]], operator.add]
    agent_trace: Annotated[list[dict[str, Any]], operator.add]
