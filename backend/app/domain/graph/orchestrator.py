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

PROMPT_SPECIALIST_NODE = "prompt_specialist"


def _enabled_custom_keys() -> list[str]:
    try:
        from app.domain.graph.agent_store import AgentStore
        from app.foundation.persistence.database import get_session_factory

        return AgentStore(get_session_factory()).list_enabled_keys()
    except Exception as exc:  # noqa: BLE001
        log.warning("orchestrator_custom_keys_unavailable: %s", exc)
        return []


def effective_ladder() -> list[str]:
    """Builtin ladder with enabled customs after corpus_fetcher."""
    customs = _enabled_custom_keys()
    base = list(FALLBACK_LADDER)
    idx = base.index("corpus_fetcher") + 1
    return base[:idx] + customs + base[idx:]


def _already_ran(agent: str, state: AgenticAnswerState) -> bool:
    return any(
        record.get("next_agent") == agent
        for record in (state.get("routing_history") or [])
    )


def _inputs_ready(agent: str, state: AgenticAnswerState, *, customs: set[str]) -> bool:
    if agent == "intent_framer":
        return bool((state.get("question") or "").strip())
    if agent == "corpus_fetcher":
        return bool(state.get("framed_query") or state.get("question"))
    if agent in customs:
        return _already_ran("corpus_fetcher", state)
    if agent == "grounded_composer":
        return _already_ran("corpus_fetcher", state)
    if agent == "source_guard":
        return bool(state.get("answer")) or bool(state.get("no_evidence"))
    return False


def _is_legal(
    target: str,
    state: AgenticAnswerState,
    *,
    order: list[str],
    customs: set[str],
) -> bool:
    if target == "finish":
        return True
    if target not in order:
        return False
    return _inputs_ready(target, state, customs=customs) and not _already_ran(
        target, state
    )


def _fallback_next(state: AgenticAnswerState, *, order: list[str] | None = None) -> str:
    ladder = order if order is not None else effective_ladder()
    customs = {k for k in ladder if k not in FALLBACK_LADDER}
    for agent in ladder:
        if _is_legal(agent, state, order=ladder, customs=customs):
            return agent
    return "finish"


def orchestrator(state: AgenticAnswerState) -> Command:
    """Route to the next specialist via ``Command(goto=...)``."""
    settings = get_settings()
    max_steps = max(1, int(settings.agentic_orchestrator_max_steps))
    step = int(state.get("supervisor_steps") or 0)
    ladder = effective_ladder()
    customs = {k for k in ladder if k not in FALLBACK_LADDER}

    if step >= max_steps:
        target = "finish"
        reason = f"step budget of {max_steps} exhausted; finishing"
        source = "limit"
        log.warning("orchestrator_step_budget_exhausted step=%s", step)
    else:
        target = _fallback_next(state, order=ladder)
        reason = f"dependency ladder selected {target!r}"
        source = "fallback"
        if not _is_legal(target, state, order=ladder, customs=customs) and target != "finish":
            overridden = target
            target = _fallback_next(state, order=ladder)
            reason = (
                f"proposed {overridden!r}, which is not legal; overridden to {target!r}"
            )
            source = "fallback"
            log.warning(
                "orchestrator_route_overridden proposed=%s chosen=%s",
                overridden,
                target,
            )

    if target == "finish":
        goto = "escalation_gate"
    elif target in customs:
        goto = PROMPT_SPECIALIST_NODE
    else:
        goto = target

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
