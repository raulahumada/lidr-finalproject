"""Prepare / normalize the user question for retrieval (memory-aware)."""

from __future__ import annotations

from typing import Any

from app.domain.graph.state import AgenticAnswerState
from app.generation.conversation.resolver import resolve


def intent_framer(state: AgenticAnswerState) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    window = list(state.get("conversation_window") or [])
    resolved = resolve(question, window)
    framed = resolved.text
    domain = str(state.get("domain") or "").strip()
    if domain and domain != "general":
        # Light retrieve bias — domain is not citable evidence.
        framed = f"[{domain}] {framed}"
    summary = (
        f"resolved follow-up using {len(resolved.substituted)} referent(s)"
        if resolved.rewritten
        else "framed query for corpus fetch"
    )
    if domain:
        summary = f"{summary}; domain={domain}"
    return {
        "framed_query": framed,
        "resolved_question": resolved.text,
        "resolved_substituted": list(resolved.substituted),
        "agent_trace": [
            {
                "node": "intent_framer",
                "summary": summary,
            }
        ],
    }
