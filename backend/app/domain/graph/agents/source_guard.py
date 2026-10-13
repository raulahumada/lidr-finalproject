"""Audit that citations refer only to retrieved hits."""

from __future__ import annotations

from typing import Any

from app.domain.graph.state import AgenticAnswerState
from app.domain.grounding import is_thin_grounding


def source_guard(state: AgenticAnswerState) -> dict[str, Any]:
    hits = state.get("hits") or []
    allowed = {int(h["chunk_id"]) for h in hits if "chunk_id" in h}
    raw_citations = state.get("citations") or []
    kept: list[dict[str, Any]] = []
    dropped = 0
    for cite in raw_citations:
        try:
            chunk_id = int(cite["chunk_id"])
        except (KeyError, TypeError, ValueError):
            dropped += 1
            continue
        if chunk_id in allowed:
            kept.append(cite)
        else:
            dropped += 1

    no_evidence = bool(state.get("no_evidence")) or not hits
    thin = is_thin_grounding(
        answer=str(state.get("answer") or ""),
        citation_count=len(kept),
        no_evidence=no_evidence,
    )
    if no_evidence:
        citations_valid = True  # empty citations on no-evidence is valid
        confidence = 0.0
    elif dropped > 0 and not kept:
        citations_valid = False
        confidence = min(float(state.get("confidence") or 0.4), 0.35)
    elif dropped > 0:
        citations_valid = False
        confidence = min(float(state.get("confidence") or 0.5), 0.45)
    else:
        citations_valid = True
        confidence = max(float(state.get("confidence") or 0.6), 0.65 if kept else 0.55)

    if thin:
        confidence = min(confidence, 0.45)

    summary = f"citations_valid={citations_valid}; kept={len(kept)}; dropped={dropped}"
    if thin:
        summary += "; thin grounding (long answer, few citations)"

    return {
        "citations": kept,
        "citations_valid": citations_valid,
        "confidence": confidence,
        "agent_trace": [
            {
                "node": "source_guard",
                "summary": summary,
            }
        ],
    }
