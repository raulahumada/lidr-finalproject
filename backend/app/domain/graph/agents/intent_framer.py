"""Prepare / normalize the user question for retrieval (v1: pass-through)."""

from __future__ import annotations

from typing import Any

from app.domain.graph.state import AgenticAnswerState


def intent_framer(state: AgenticAnswerState) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    return {
        "framed_query": question,
        "agent_trace": [
            {
                "node": "intent_framer",
                "summary": "framed query for corpus fetch",
            }
        ],
    }
