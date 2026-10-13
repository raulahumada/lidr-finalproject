from __future__ import annotations

from langgraph.types import Command

from app.config import get_settings
from app.domain.graph.orchestrator import (
    FALLBACK_LADDER,
    _fallback_next,
    effective_ladder,
    orchestrator,
)


def test_ladder_starts_with_intent_framer(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: [],
    )
    assert _fallback_next({"question": "hola", "routing_history": []}) == "intent_framer"


def test_ladder_advances_after_framer(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: [],
    )
    state = {
        "question": "hola",
        "framed_query": "hola",
        "routing_history": [{"next_agent": "intent_framer"}],
    }
    assert _fallback_next(state) == "corpus_fetcher"


def test_ladder_finishes_after_scope_pin(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: [],
    )
    state = {
        "question": "De acá en adelante solo cobranzas",
        "framed_query": "De acá en adelante solo cobranzas",
        "scope_pin_only": True,
        "answer": "Entendido.",
        "routing_history": [{"next_agent": "intent_framer"}],
    }
    assert _fallback_next(state) == "finish"


def test_effective_ladder_inserts_customs_after_corpus(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: ["risk_advisor"],
    )
    ladder = effective_ladder()
    assert ladder.index("corpus_fetcher") < ladder.index("risk_advisor")
    assert ladder.index("risk_advisor") < ladder.index("grounded_composer")
    assert set(FALLBACK_LADDER).issubset(set(ladder))


def test_orchestrator_routes_custom_to_prompt_specialist(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_ORCHESTRATOR_MAX_STEPS", "10")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: ["risk_advisor"],
    )
    cmd = orchestrator(
        {
            "question": "hola",
            "framed_query": "hola",
            "routing_history": [
                {"next_agent": "intent_framer"},
                {"next_agent": "corpus_fetcher"},
            ],
            "supervisor_steps": 2,
        }
    )
    assert cmd.goto == "prompt_specialist"
    assert cmd.update["routing_history"][0]["next_agent"] == "risk_advisor"


def test_orchestrator_returns_command(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_ORCHESTRATOR_MAX_STEPS", "10")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: [],
    )
    cmd = orchestrator({"question": "hola", "routing_history": [], "supervisor_steps": 0})
    assert isinstance(cmd, Command)
    assert cmd.goto == "intent_framer"
    assert cmd.update["routing_history"][0]["next_agent"] == "intent_framer"


def test_orchestrator_budget_forces_gate(monkeypatch) -> None:
    monkeypatch.setenv("AGENTIC_ORCHESTRATOR_MAX_STEPS", "2")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.domain.graph.orchestrator._enabled_custom_keys",
        lambda: [],
    )
    cmd = orchestrator(
        {
            "question": "hola",
            "routing_history": [],
            "supervisor_steps": 2,
        }
    )
    assert cmd.goto == "escalation_gate"
    assert cmd.update["routing_history"][0]["source"] == "limit"
