"""Render a budgeted conversation-memory block (evidence always wins)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.generation.rag.context_blocks import count_tokens

_HEADER = (
    "Memoria de la conversación (contexto del hilo, NUNCA procedencia: "
    "citá solo el contexto recuperado del corpus):"
)


@dataclass(frozen=True)
class MemoryBlock:
    text: str
    turns_included: int
    turns_dropped: int
    tokens_used: int

    @property
    def trimmed(self) -> bool:
        return self.turns_dropped > 0


def _turn_lines(index: int, question: str, answer: str) -> list[str]:
    return [
        f"- Turno {index}:",
        f"  Pregunta: {question}",
        f"  Respuesta: {answer}",
    ]


def render_memory(
    window: list[dict[str, Any]] | None,
    *,
    budget: int,
    answer_preview_chars: int = 400,
) -> MemoryBlock | None:
    """Render recent turns trimmed to ``budget`` tokens.

    Returns ``None`` when there is nothing to remember so callers keep the
    no-session path identical. Drops oldest turns first.
    """
    if not window:
        return None

    def _render(turns: list[dict[str, Any]]) -> str:
        lines = [_HEADER]
        for index, turn in enumerate(turns, start=1):
            question = str(
                turn.get("resolved_question") or turn.get("question") or ""
            ).strip()
            answer = str(turn.get("answer") or "").strip()
            if answer_preview_chars > 0:
                answer = answer[:answer_preview_chars]
            lines.extend(_turn_lines(index, question, answer))
        return "\n".join(lines)

    turns = list(window)
    turns_dropped = 0
    # Drop oldest first, but keep at least the newest turn (follow-ups lean on it)
    # even if that alone exceeds the budget — same honesty idea as peer facts.
    while len(turns) > 1 and count_tokens(_render(turns)) > budget:
        turns.pop(0)
        turns_dropped += 1

    text = _render(turns)
    return MemoryBlock(
        text=text,
        turns_included=len(turns),
        turns_dropped=turns_dropped,
        tokens_used=count_tokens(text),
    )
