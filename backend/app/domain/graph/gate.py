"""Conditional human escalation — interrupt only when review_reasons is non-empty."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.types import interrupt

from app.config import Settings, get_settings
from app.domain.graph.state import AgenticAnswerState

log = logging.getLogger(__name__)


def review_reasons(
    state: AgenticAnswerState, settings: Settings | None = None
) -> list[str]:
    """Pure trigger list. Empty → ship without interrupt."""
    settings = settings or get_settings()
    # Meta scope pin — confirmation only; corpus evidence is not expected.
    if state.get("scope_pin_only"):
        return []

    reasons: list[str] = []

    confidence = state.get("confidence")
    threshold = settings.agentic_confidence_threshold
    if confidence is not None and confidence < threshold:
        reasons.append(
            f"confidence {confidence:.2f} is below the {threshold:.2f} threshold"
        )

    if state.get("citations_valid") is False:
        reasons.append("citations do not match retrieved corpus hits")

    if state.get("no_evidence") or not (state.get("hits") or []):
        reasons.append("no evidence was retrieved for this question in the corpus")

    return reasons


def _apply_decision(
    state: AgenticAnswerState, decision: dict[str, Any]
) -> dict[str, Any]:
    action = (
        (decision or {}).get("decision")
        or (decision or {}).get("action")
        or "approve"
    )
    update: dict[str, Any] = {
        "human_decision": decision or {},
        "needs_human_review": True,
    }
    if action == "reject":
        update["status"] = "rejected"
        return update
    if action == "adjust":
        adjusted = (decision or {}).get("adjusted_answer")
        if isinstance(adjusted, str) and adjusted.strip():
            update["answer"] = adjusted.strip()
        update["status"] = "completed"
        update["citations_valid"] = True
        return update
    update["status"] = "completed"
    update["citations_valid"] = bool(state.get("citations_valid", True))
    return update


def escalation_gate(state: AgenticAnswerState) -> dict[str, Any]:
    """Pause for a human when triggers fire; otherwise mark completed."""
    reasons = review_reasons(state)
    if not reasons:
        log.info(
            "escalation_gate_skipped confidence=%s citations_valid=%s",
            state.get("confidence"),
            state.get("citations_valid"),
        )
        return {
            "needs_human_review": False,
            "review_reasons": [],
            "status": "completed",
            "agent_trace": [
                {
                    "node": "escalation_gate",
                    "summary": "no review reasons — completed",
                }
            ],
        }

    decision = interrupt(
        {
            "gate": "escalation",
            "question": state.get("question"),
            "reasons": reasons,
            "confidence": state.get("confidence"),
            "answer": state.get("answer"),
            "citations": state.get("citations") or [],
        }
    )
    decision = decision if isinstance(decision, dict) else {}
    update = _apply_decision(state, decision)
    action = decision.get("decision") or decision.get("action") or "approve"
    update["review_reasons"] = reasons
    update["agent_trace"] = [
        {
            "node": "escalation_gate",
            "summary": f"human {action}",
        }
    ]
    log.info("escalation_gate_resumed action=%s reasons=%s", action, len(reasons))
    return update
