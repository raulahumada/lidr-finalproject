"""Prepare / normalize the user question for retrieval (memory-aware)."""

from __future__ import annotations

from typing import Any

from app.domain.graph.state import AgenticAnswerState
from app.generation.conversation.resolver import resolve


def intent_framer(state: AgenticAnswerState) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    window = list(state.get("conversation_window") or [])
    resolved = resolve(question, window)
    summary = (
        f"resolved follow-up using {len(resolved.substituted)} referent(s)"
        if resolved.rewritten
        else "framed query for corpus fetch"
    )
    return {
        "framed_query": resolved.text,
        "resolved_question": resolved.text,
        "resolved_substituted": list(resolved.substituted),
        "agent_trace": [
            {
                "node": "intent_framer",
                "summary": summary,
            }
        ],
    }
