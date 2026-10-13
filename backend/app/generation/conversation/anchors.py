"""Detect explicit conversation-scope pins (heuristic ES, no LLM).

Both halves are required: a scoping phrase AND a concrete Metropol domain the
retriever already understands. Prefer miss over silently emptying later search.
"""

from __future__ import annotations

import re

from app.domain.graph.domain_tag import DOMAINS
from app.generation.conversation.models import Anchor

# Phrase must SCOPE, not merely mention. "en cobranzas" filters one question;
# "de acá en adelante, cobranzas" pins the conversation.
_SCOPING_PHRASE = re.compile(
    r"\b("
    r"de (?:ac[áa]|aqu[íi]|ahora) en (?:adelante|m[áa]s)"
    r"|de ahora en (?:adelante|m[áa]s)"
    r"|para (?:todo|el resto de) (?:lo que sigue|la conversaci[óo]n|las (?:pr[óo]ximas )?preguntas)"
    r"|(?:siempre|solo|s[óo]lo|[úu]nicamente) (?:en |de |para |dentro de )?"
    r"(?:el |la |los |las )?(?:dominio |tema )?"
    r"(?:cobranzas?|ventas?|tenela|operaci[oó]n|omnicanal(?:idad)?)"
    r"|limit[áa](?:te)?(?: solo| s[óo]lo)? a"
    r"|qued[áa](?:te)?(?: solo| s[óo]lo)? (?:en|con)"
    r")\b",
    re.IGNORECASE,
)

_DOMAIN_TOKEN = re.compile(
    r"\b("
    r"cobranzas?|ventas?|tenela|operaci[oó]n|omnicanal(?:idad)?"
    r")\b",
    re.IGNORECASE,
)

_DOMAIN_ALIASES: dict[str, str] = {
    "cobranza": "cobranzas",
    "cobranzas": "cobranzas",
    "venta": "ventas",
    "ventas": "ventas",
    "tenela": "tenela",
    "operacion": "operacion",
    "operación": "operacion",
    "omnicanal": "operacion",
    "omnicanalidad": "operacion",
}

_ALLOWED = {d for d in DOMAINS if d != "general"}


def detect_anchors(question: str) -> list[Anchor]:
    """Constraints this question pins, if any.

    A scoping phrase without a pinable domain yields nothing — e.g.
    "de acá en adelante sé más breve" is not a retrieve filter.
    """
    text = (question or "").strip()
    if not text or not _SCOPING_PHRASE.search(text):
        return []

    anchors: list[Anchor] = []
    seen: set[str] = set()
    for match in _DOMAIN_TOKEN.finditer(text):
        raw = match.group(1).casefold()
        # Normalize accented operacion from regex group
        normalized = _DOMAIN_ALIASES.get(raw) or _DOMAIN_ALIASES.get(
            raw.replace("ó", "o")
        )
        if not normalized or normalized not in _ALLOWED or normalized in seen:
            continue
        seen.add(normalized)
        anchors.append(
            Anchor(kind="domain", value=normalized, source_question=text)
        )
    return anchors


def pinned_domain(anchors: list[Anchor] | list[dict] | None) -> str | None:
    """Most recent domain anchor value, or None."""
    if not anchors:
        return None
    for item in reversed(list(anchors)):
        if isinstance(item, Anchor):
            if item.kind == "domain" and item.value in _ALLOWED:
                return item.value
            continue
        if isinstance(item, dict) and item.get("kind") == "domain":
            value = str(item.get("value") or "").strip().lower()
            if value in _ALLOWED:
                return value
    return None


# Content asks mean the turn is not "pin only" — still record anchors, but RAG.
_CONTENT_ASK = re.compile(
    r"\b("
    r"c[oó]mo|qu[eé]|cu[aá]l(?:es)?|cu[aá]ndo|d[oó]nde|"
    r"por\s+qu[eé]|explic[ae]|cont[ae]|dame|decime|"
    r"necesito|quiero\s+saber|en\s+qu[eé]\s+consiste"
    r")\b",
    re.IGNORECASE,
)


def is_scope_pin_only(question: str) -> bool:
    """True when the utterance only pins scope (no corpus question).

    "De acá en adelante solo cobranzas" → True.
    "De acá en adelante solo cobranzas, ¿cómo es el handoff?" → False
    (anchor still detected separately).
    """
    text = (question or "").strip()
    if not text or not detect_anchors(text):
        return False
    return _CONTENT_ASK.search(text) is None


def acknowledge_scope_pin(anchors: list[Anchor]) -> str:
    """Short confirmation — no corpus dump."""
    domains = [a.value for a in anchors if a.kind == "domain" and a.value]
    if not domains:
        return (
            "Entendido. Quedó registrado el alcance de la conversación. "
            "¿Qué querés consultar?"
        )
    if len(domains) == 1:
        return (
            f"Entendido. De acá en adelante acoto el alcance a {domains[0]}. "
            "Preguntame lo que necesites sobre ese dominio."
        )
    joined = ", ".join(domains)
    return (
        f"Entendido. De acá en adelante acoto el alcance a: {joined}. "
        "Preguntame lo que necesites."
    )
