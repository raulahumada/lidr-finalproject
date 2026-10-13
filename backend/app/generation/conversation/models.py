"""Metropol session memory shapes: facts + anchors (no LLM extract).

Facts are small structured state re-rendered into the prompt each turn.
Anchors are explicit scoping pins the user set on purpose — forgetting one
silently widens later retrieve, so the sliding window never evicts them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

AnchorKind = Literal["domain"]


def _union(current: list[str], incoming: list[str]) -> list[str]:
    merged = list(current)
    seen = {value.casefold() for value in merged}
    for value in incoming:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        if cleaned.casefold() not in seen:
            merged.append(cleaned)
            seen.add(cleaned.casefold())
    return merged


@dataclass
class ConversationFacts:
    """Durable facts derived from turn outputs (domain, citations, entities)."""

    domains: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    last_document_ids: list[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not (self.domains or self.entities or self.last_document_ids)

    def merge_with(self, update: ConversationFacts) -> ConversationFacts:
        """Union accumulating lists; replace last_document_ids when non-empty."""
        return ConversationFacts(
            domains=_union(self.domains, update.domains),
            entities=_union(self.entities, update.entities),
            last_document_ids=update.last_document_ids or self.last_document_ids,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "domains": list(self.domains),
            "entities": list(self.entities),
            "last_document_ids": list(self.last_document_ids),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> ConversationFacts:
        if not isinstance(raw, dict):
            return cls()
        return cls(
            domains=[str(x) for x in (raw.get("domains") or []) if str(x).strip()],
            entities=[str(x) for x in (raw.get("entities") or []) if str(x).strip()],
            last_document_ids=[
                str(x) for x in (raw.get("last_document_ids") or []) if str(x).strip()
            ],
        )


@dataclass(frozen=True)
class Anchor:
    """A retrieval-usable scope pin (Metropol domain only)."""

    kind: AnchorKind
    value: str
    source_question: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "value": self.value,
            "source_question": self.source_question,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> Anchor | None:
        if not isinstance(raw, dict):
            return None
        kind = str(raw.get("kind") or "").strip()
        value = str(raw.get("value") or "").strip().lower()
        if kind != "domain" or not value or value == "general":
            return None
        return cls(
            kind="domain",
            value=value,
            source_question=str(raw.get("source_question") or ""),
        )


@dataclass
class SessionMemory:
    """Persisted bag: facts + anchors for one conversation session."""

    facts: ConversationFacts = field(default_factory=ConversationFacts)
    anchors: list[Anchor] = field(default_factory=list)

    def is_empty(self) -> bool:
        return self.facts.is_empty() and not self.anchors

    def to_dict(self) -> dict[str, Any]:
        return {
            "facts": self.facts.to_dict(),
            "anchors": [a.to_dict() for a in self.anchors],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any] | None) -> SessionMemory:
        if not isinstance(raw, dict):
            return cls()
        anchors: list[Anchor] = []
        for item in raw.get("anchors") or []:
            parsed = Anchor.from_dict(item if isinstance(item, dict) else None)
            if parsed is not None:
                anchors.append(parsed)
        return cls(
            facts=ConversationFacts.from_dict(
                raw.get("facts") if isinstance(raw.get("facts"), dict) else None
            ),
            anchors=anchors,
        )


def merge_anchors(current: list[Anchor], incoming: list[Anchor]) -> list[Anchor]:
    """Union anchors by (kind, value); preserve first-seen order."""
    merged = list(current)
    seen = {(a.kind, a.value.casefold()) for a in merged}
    for anchor in incoming:
        key = (anchor.kind, anchor.value.casefold())
        if key not in seen:
            merged.append(anchor)
            seen.add(key)
    return merged
