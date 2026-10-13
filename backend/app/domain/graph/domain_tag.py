"""Metropol business-domain tag for an agentic run (not a LangGraph agent)."""

from __future__ import annotations

import re
from typing import Literal

MetropolDomain = Literal["ventas", "cobranzas", "operacion", "tenela", "general"]

DOMAINS: tuple[MetropolDomain, ...] = (
    "ventas",
    "cobranzas",
    "operacion",
    "tenela",
    "general",
)

_PATTERNS: list[tuple[MetropolDomain, re.Pattern[str]]] = [
    (
        "tenela",
        re.compile(
            r"\btenela\b|\bdictamen\b|\bsimulaci[oó]n\b|\bidentidad\b|\bcore\b",
            re.IGNORECASE,
        ),
    ),
    (
        "cobranzas",
        re.compile(
            r"\bcobranzas?\b|\bmora\b|\bquita\b|\bpromesa(?:s)?\b|\bpago(?:s)?\b|"
            r"\bhandoff\b.*\bcobr|\bcobr.*\bhandoff\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ventas",
        re.compile(
            r"\bventas?\b|\boferta(?:s)?\b|\bcaptaci[oó]n\b|\bsolicitud(?:es)?\b|"
            r"\bprospecto(?:s)?\b|\bcr[eé]dito\b",
            re.IGNORECASE,
        ),
    ),
    (
        "operacion",
        re.compile(
            r"\bomnicanal(?:idad)?\b|\bwhatsapp\b|\bcampañ(?:a|as)\b|\bcanal(?:es)?\b|"
            r"\bhandoff\b|\boperaci[oó]n\b",
            re.IGNORECASE,
        ),
    ),
]


def parse_domain(value: str | None) -> MetropolDomain | None:
    """Return a valid domain or None if empty; raise ValueError if invalid."""
    if value is None:
        return None
    cleaned = value.strip().lower()
    if not cleaned or cleaned == "auto":
        return None
    if cleaned not in DOMAINS:
        raise ValueError(f"Unsupported domain: {value!r}")
    return cleaned  # type: ignore[return-value]


def detect_domain(question: str, *, window: list[dict] | None = None) -> MetropolDomain:
    """Heuristic domain from the question (and optional prior turns)."""
    parts = [question or ""]
    for turn in window or []:
        parts.append(str(turn.get("question") or ""))
        parts.append(str(turn.get("resolved_question") or ""))
    text = " ".join(parts)
    for domain, pattern in _PATTERNS:
        if pattern.search(text):
            return domain
    return "general"
