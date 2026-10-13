"""Star-topology hub: deterministic ladder + step budget (Cristian-shaped)."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.types import Command

from app.config import get_settings
from app.domain.graph.state import AgenticAnswerState

log = logging.getLogger(__name__)

FALLBACK_LADDER = (
    "intent_framer",
    "corpus_fetcher",
    "grounded_composer",
    "source_guard",
)
_ORDER = list(FALLBACK_LADDER)


def _already_ran(agent: str, state: AgenticAnswerState) -> bool:
    return any(
        record.get("next_agent") == agent
        for record in (state.get("routing_history") or [])
    )


def _inputs_ready(agent: str, state: AgenticAnswerState) -> bool:
    if agent == "intent_framer":
        return bool((state.get("question") or "").strip())
    if agent == "corpus_fetcher":
        return bool(state.get("framed_query") or state.get("question"))
    if agent == "grounded_composer":
        return _already_ran("corpus_fetcher", state)
    if agent == "source_guard":
        return bool(state.get("answer")) or bool(state.get("no_evidence"))
    return False


def _is_legal(target: str, state: AgenticAnswerState) -> bool:
    if target == "finish":
        return True
    if target not in _ORDER:
        return False
    return _inputs_ready(target, state) and not _already_ran(target, state)


def _fallback_next(state: AgenticAnswerState) -> str:
    for agent in _ORDER:
        if _is_legal(agent, state):
            return agent
    return "finish"


def orchestrator(state: AgenticAnswerState) -> Command:
    """Route to the next specialist via ``Command(goto=...)``."""
    settings = get_settings()
    max_steps = max(1, int(settings.agentic_orchestrator_max_steps))
    step = int(state.get("supervisor_steps") or 0)

    if step >= max_steps:
        target = "finish"
        reason = f"step budget of {max_steps} exhausted; finishing"
        source = "limit"
        log.warning("orchestrator_step_budget_exhausted step=%s", step)
    else:
        target = _fallback_next(state)
        reason = f"dependency ladder selected {target!r}"
        source = "fallback"
        if not _is_legal(target, state) and target != "finish":
            overridden = target
            target = _fallback_next(state)
            reason = (
                f"proposed {overridden!r}, which is not legal; overridden to {target!r}"
            )
            source = "fallback"
            log.warning(
                "orchestrator_route_overridden proposed=%s chosen=%s",
                overridden,
                target,
            )

    goto = "escalation_gate" if target == "finish" else target
    update: dict[str, Any] = {
        "next_agent": target,
        "route_reason": reason,
        "supervisor_steps": step + 1,
        "routing_history": [
            {
                "step": step,
                "next_agent": target,
                "reason": reason,
                "source": source,
            }
        ],
        "agent_trace": [
            {
                "node": "orchestrator",
                "summary": f"route → {target} ({source})",
            }
        ],
    }
    log.info(
        "orchestrator_route step=%s next=%s goto=%s source=%s",
        step,
        target,
        goto,
        source,
    )
    return Command(goto=goto, update=update)
