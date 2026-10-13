from __future__ import annotations

from app.generation.conversation.resolver import resolve


def test_empty_window_is_noop() -> None:
    result = resolve("¿y con Tenela?", [])
    assert result.text == "¿y con Tenela?"
    assert result.substituted == []
    assert not result.rewritten


def test_self_contained_question_unchanged() -> None:
    window = [
        {
            "question": "¿Cómo es el handoff de cobranzas?",
            "answer": "Se escala a Tenela.",
        }
    ]
    q = "¿Cómo funciona el dictamen de crédito en Tenela?"
    result = resolve(q, window)
    assert result.text == q
    assert result.substituted == []


def test_referential_follow_up_rewritten() -> None:
    window = [
        {
            "question": "¿Cómo es el handoff de cobranzas con Tenela?",
            "answer": "Se deriva al core.",
        }
    ]
    result = resolve("¿y eso también aplica a ventas?", window)
    assert result.rewritten
    assert "handoff de cobranzas" in result.text.lower() or "Tenela" in result.text
    assert result.substituted
