from __future__ import annotations

from langgraph.types import Command

from app.config import get_settings
from app.domain.graph.orchestrator import _fallback_next, orchestrator


def test_ladder_starts_with_intent_framer() -> None:
    assert _fallback_next({"question": "hola", "routing_history": []}) == "intent_framer"


def test_ladder_advances_after_framer() -> None:
    state = {
        "question": "hola",
        "framed_query": "hola",
        "routing_history": [{"next_agent": "intent_framer"}],
    }
    assert _fallback_next(state) == "corpus_fetcher"


def test_orchestrator_returns_command(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_ORCHESTRATOR_MAX_STEPS", "10")
    get_settings.cache_clear()
    cmd = orchestrator({"question": "hola", "routing_history": [], "supervisor_steps": 0})
    assert isinstance(cmd, Command)
    assert cmd.goto == "intent_framer"
    assert cmd.update["routing_history"][0]["next_agent"] == "intent_framer"


def test_orchestrator_budget_forces_gate(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_ORCHESTRATOR_MAX_STEPS", "2")
    get_settings.cache_clear()
    cmd = orchestrator(
        {
            "question": "hola",
            "routing_history": [],
            "supervisor_steps": 2,
        }
    )
    assert cmd.goto == "escalation_gate"
    assert cmd.update["routing_history"][0]["source"] == "limit"
