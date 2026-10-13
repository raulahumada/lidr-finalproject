from __future__ import annotations

from app.generation.conversation.budget import render_memory


def test_empty_window_returns_none() -> None:
    assert render_memory([], budget=1024) is None
    assert render_memory(None, budget=1024) is None


def test_memory_fits_under_budget() -> None:
    window = [
        {
            "question": "¿Cómo es el handoff?",
            "answer": "Se escala a un humano.",
        }
    ]
    block = render_memory(window, budget=1024)
    assert block is not None
    assert block.turns_included == 1
    assert block.turns_dropped == 0
    assert "Memoria de la conversación" in block.text
    assert "handoff" in block.text


def test_oldest_turns_trimmed_first() -> None:
    window = [
        {"question": f"pregunta vieja {i}", "answer": ("respuesta " * 40) + str(i)}
        for i in range(6)
    ]
    block = render_memory(window, budget=80)
    assert block is not None
    assert block.trimmed
    assert block.turns_dropped >= 1
    assert "pregunta vieja 5" in block.text
    assert "pregunta vieja 0" not in block.text
