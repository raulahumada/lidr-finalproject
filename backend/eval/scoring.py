"""Pure scoring of agentic answer payloads against golden-set cases."""

from __future__ import annotations

from typing import Any


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def score_case(
    case: dict[str, Any],
    payload: dict[str, Any],
    *,
    pause_status: str | None = None,
) -> dict[str, Any]:
    """Return ``{passed, reasons, case_id}`` for one case vs one payload.

    ``pause_status`` is the status observed *before* an optional auto-approve
    resume; used only for ``expect_pause``.
    """
    reasons: list[str] = []
    case_id = str(case.get("id") or "")
    answer = str(payload.get("answer") or "")
    answer_l = answer.lower()
    status = str(payload.get("status") or "")
    citations = payload.get("citations") or []
    if not isinstance(citations, list):
        citations = []
    citations_valid = payload.get("citations_valid")
    no_evidence = bool(payload.get("no_evidence"))

    if _as_bool(case.get("expect_citations")):
        if len(citations) < 1:
            reasons.append("expected citations but payload has none")
        if citations_valid is False:
            reasons.append("citations_valid is false")

    if _as_bool(case.get("expect_no_evidence")) and not no_evidence:
        reasons.append("expected no_evidence=true")

    if _as_bool(case.get("expect_pause")):
        observed = pause_status if pause_status is not None else status
        if observed != "awaiting_human_review":
            reasons.append(
                f"expected pause awaiting_human_review, got {observed!r}"
            )

    for needle in case.get("must_mention") or []:
        text = str(needle).strip()
        if not text:
            continue
        if not answer_l or text.lower() not in answer_l:
            reasons.append(f"answer missing required mention: {text!r}")

    for needle in case.get("must_not_mention") or []:
        text = str(needle).strip()
        if not text:
            continue
        if text.lower() in answer_l:
            reasons.append(f"answer contains forbidden mention: {text!r}")

    return {
        "case_id": case_id,
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "status": status,
        "citation_count": len(citations),
        "no_evidence": no_evidence,
        "citations_valid": citations_valid,
    }
