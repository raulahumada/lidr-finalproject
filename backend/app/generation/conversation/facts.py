"""Derive session facts from turn outputs — no second LLM call."""

from __future__ import annotations

import re
from typing import Any

from app.generation.conversation.models import ConversationFacts

# Light entity tokens that show up in Metropol Q&A and help resolve follow-ups.
_ENTITY = re.compile(
    r"\b("
    r"tenela|whatsapp|omnicanalidad|handoff|dictamen|quita|mora|"
    r"promesa(?:s)?|captaci[oó]n"
    r")\b",
    re.IGNORECASE,
)


def entities_in(text: str) -> list[str]:
    """Entity-shaped tokens in ``text``, lower-cased, first-seen order."""
    found: list[str] = []
    seen: set[str] = set()
    for match in _ENTITY.finditer(text or ""):
        token = match.group(1).casefold()
        if token not in seen:
            seen.add(token)
            found.append(token)
    return found


def facts_from_turn(
    *,
    question: str,
    domain: str | None,
    citations: list[dict[str, Any]] | None,
) -> ConversationFacts:
    """Facts this turn establishes before merging with the session bag."""
    domains: list[str] = []
    cleaned = (domain or "").strip().lower()
    if cleaned and cleaned != "general":
        domains.append(cleaned)

    doc_ids: list[str] = []
    seen: set[str] = set()
    for item in citations or []:
        if not isinstance(item, dict):
            continue
        raw = item.get("document_id")
        if raw is None:
            continue
        doc_id = str(raw).strip()
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            doc_ids.append(doc_id)

    return ConversationFacts(
        domains=domains,
        entities=entities_in(question),
        last_document_ids=doc_ids,
    )
