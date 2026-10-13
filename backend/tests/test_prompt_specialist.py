from __future__ import annotations

from app.domain.graph.agents.prompt_specialist import prompt_specialist


class _StubChat:
    def complete_json(self, *, system: str, user: str) -> dict:
        assert "asesor" in system.lower() or system
        return {"note": "revisá mora y promesas"}


def test_prompt_specialist_uses_stub_chat(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.domain.graph.agent_store.AgentStore.get_system_prompt",
        lambda self, key: "Sos un asesor de riesgo.",
    )
    out = prompt_specialist(
        {
            "next_agent": "risk_advisor",
            "question": "¿Qué riesgo hay en cobranzas?",
            "hits": [{"excerpt": "handoff Tenela"}],
        },
        {"configurable": {"chat": _StubChat()}},
    )
    assert out["custom_notes"][0]["key"] == "risk_advisor"
    assert "mora" in out["custom_notes"][0]["note"]
    assert out["agent_trace"][0]["node"] == "prompt_specialist"
