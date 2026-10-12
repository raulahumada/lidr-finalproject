"""Shared state for the Metropol agentic answer graph."""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgenticAnswerState(TypedDict, total=False):
    question: str
    k: int
    framed_query: str
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
    agent_trace: Annotated[list[dict[str, Any]], operator.add]
