"""Shared abstention copy for sync answer and agentic grounded composition."""

from __future__ import annotations

# Deterministic no-LLM template when retrieve is empty / no_evidence.
# Keep short: must not look like an invented operational procedure.
NO_EVIDENCE_ANSWER = (
    "No encontré evidencia suficiente en el corpus Metropol para responder "
    "con confianza. No invento procedimientos ni pasos operativos sin respaldo "
    "en la documentación recuperada. "
    "Recomendación: reformular la pregunta o escalar a un humano."
)

# Light heuristic: long prose with almost no citations often means elaboration.
LONG_ANSWER_CHARS = 700
FEW_CITATIONS_MAX = 1


def is_thin_grounding(*, answer: str, citation_count: int, no_evidence: bool) -> bool:
    """True when the answer is long but barely cited (review / confidence cue)."""
    if no_evidence:
        return False
    text = (answer or "").strip()
    return len(text) >= LONG_ANSWER_CHARS and citation_count <= FEW_CITATIONS_MAX
