"""Resolve referential follow-ups before retrieval (Cristian-shaped, Metropol).

Deterministic and conservative: a wrong expansion produces a confident wrong
search. Prefer leaving the question untouched over inventing a referent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

MAX_REFERENTS = 2
_PRIOR_SNIPPET_MAX = 120

# Markers that the question leans on a previous turn (determiner vs pronoun).
_END_OF_CLAUSE = r"(?=\s*(?:[?!.,;:)]|$))"
_REFERENTIAL = re.compile(
    r"(^\s*¿?\s*y\b)"
    r"|\b(eso|aquello)\b"
    rf"|\b(esa|ese|esos|esas)\b{_END_OF_CLAUSE}"
    rf"|\b(la|el) mism[ao]\b{_END_OF_CLAUSE}"
    r"|\blo anterior\b"
    r"|\ball[íi]\b"
    r"|\bah[íi]\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ResolvedQuestion:
    """Question to retrieve with, plus what was substituted (if any)."""

    text: str
    substituted: list[str]

    @property
    def rewritten(self) -> bool:
        return bool(self.substituted)


def _snippet(text: str, *, max_len: int = _PRIOR_SNIPPET_MAX) -> str:
    cleaned = " ".join((text or "").strip().split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def _referents_from_window(window: list[dict[str, Any]]) -> list[str]:
    if not window:
        return []
    last = window[-1]
    prior = str(last.get("resolved_question") or last.get("question") or "").strip()
    named: list[str] = []
    if prior:
        named.append(_snippet(prior))
    for cite in last.get("citations") or []:
        path = str(cite.get("source_path") or "").strip()
        if not path:
            continue
        leaf = path.rsplit("/", 1)[-1]
        if leaf and leaf not in named:
            named.append(_snippet(leaf, max_len=80))
        if len(named) >= MAX_REFERENTS:
            break
    return named[:MAX_REFERENTS]


def resolve(
    question: str,
    window: list[dict[str, Any]] | None,
) -> ResolvedQuestion:
    """Name the referent when the question only points at the prior turn."""
    text = (question or "").strip()
    if not text or not window:
        return ResolvedQuestion(text=text, substituted=[])

    if not _REFERENTIAL.search(text):
        return ResolvedQuestion(text=text, substituted=[])

    named = _referents_from_window(window)
    if not named:
        return ResolvedQuestion(text=text, substituted=[])

    resolved = f"{text} (sobre {', '.join(named)})"
    return ResolvedQuestion(text=resolved, substituted=named)
