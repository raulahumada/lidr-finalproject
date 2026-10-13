"""Prepare / normalize the user question for retrieval (memory-aware)."""

from __future__ import annotations

from typing import Any

from app.domain.graph.state import AgenticAnswerState
from app.generation.conversation.anchors import (
    acknowledge_scope_pin,
    detect_anchors,
    is_scope_pin_only,
    pinned_domain,
)
from app.generation.conversation.models import Anchor, merge_anchors
from app.generation.conversation.resolver import resolve


def intent_framer(state: AgenticAnswerState) -> dict[str, Any]:
    question = (state.get("question") or "").strip()
    window = list(state.get("conversation_window") or [])
    facts = state.get("conversation_facts")
    prior_anchors = list(state.get("conversation_anchors") or [])

    # Meta turn: pin scope only — confirm and skip retrieve/compose.
    if is_scope_pin_only(question):
        new_anchors = detect_anchors(question)
        prior_parsed: list[Anchor] = []
        for item in prior_anchors:
            if isinstance(item, Anchor):
                prior_parsed.append(item)
            elif isinstance(item, dict):
                parsed = Anchor.from_dict(item)
                if parsed is not None:
                    prior_parsed.append(parsed)
        merged = merge_anchors(prior_parsed, new_anchors)
        domain = (
            pinned_domain(new_anchors)
            or str(state.get("domain") or "").strip()
            or "general"
        )
        return {
            "framed_query": question,
            "resolved_question": question,
            "resolved_substituted": [],
            "scope_pin_only": True,
            "domain": domain,
            "conversation_anchors": [a.to_dict() for a in merged],
            "answer": acknowledge_scope_pin(new_anchors),
            "citations": [],
            "citations_valid": True,
            "confidence": 1.0,
            "no_evidence": False,
            "hits": [],
            "agent_trace": [
                {
                    "node": "intent_framer",
                    "summary": (
                        f"scope pin only — skip retrieve; "
                        f"domain={domain}; anchors={len(new_anchors)}"
                    ),
                }
            ],
        }

    resolved = resolve(
        question, window, facts=facts, anchors=prior_anchors
    )
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
    if prior_anchors:
        summary = f"{summary}; anchors={len(prior_anchors)}"
    return {
        "framed_query": framed,
        "resolved_question": resolved.text,
        "resolved_substituted": list(resolved.substituted),
        "scope_pin_only": False,
        "agent_trace": [
            {
                "node": "intent_framer",
                "summary": summary,
            }
        ],
    }
