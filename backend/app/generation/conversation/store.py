"""Postgres-backed conversation session store."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.foundation.persistence.models import ConversationSessionRow
from app.generation.conversation.models import (
    Anchor,
    ConversationFacts,
    SessionMemory,
    merge_anchors,
)

_TITLE_MAX = 80

# Sentinel: skip ownership filter (internal runner after API already scoped).
_UNSCOPED = object()


class SessionNotFoundError(KeyError):
    """Raised when a session_id was never minted or was deleted."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _truncate_title(question: str) -> str:
    text = " ".join(question.strip().split())
    if len(text) <= _TITLE_MAX:
        return text
    return text[: _TITLE_MAX - 1].rstrip() + "…"


def _visible(row: ConversationSessionRow, owner_id: str | None) -> bool:
    if owner_id is None:
        return row.owner_id is None
    return row.owner_id == owner_id


class SessionStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, *, owner_id: str | None = None) -> dict[str, Any]:
        session_id = uuid.uuid4().hex
        now = _utcnow()
        with self._session_factory() as db:
            row = ConversationSessionRow(
                id=session_id,
                title=None,
                owner_id=owner_id,
                history=[],
                memory={},
                created_at=now,
                updated_at=now,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return self._to_view(row)

    def list_summaries(self, *, owner_id: str | None = None) -> list[dict[str, Any]]:
        with self._session_factory() as db:
            stmt = select(ConversationSessionRow).order_by(
                ConversationSessionRow.updated_at.desc()
            )
            if owner_id is None:
                stmt = stmt.where(ConversationSessionRow.owner_id.is_(None))
            else:
                stmt = stmt.where(ConversationSessionRow.owner_id == owner_id)
            rows = db.scalars(stmt).all()
            return [
                {
                    "session_id": row.id,
                    "title": row.title,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "turn_count": len(row.history or []),
                }
                for row in rows
            ]

    def get(
        self,
        session_id: str,
        *,
        owner_id: Any = _UNSCOPED,
    ) -> dict[str, Any] | None:
        """Load a session.

        Pass ``owner_id=...`` (including ``None`` for the unowned bucket) to
        enforce scope. Omit ``owner_id`` for unchecked access (agentic runner).
        """
        with self._session_factory() as db:
            row = db.get(ConversationSessionRow, session_id)
            if row is None:
                return None
            if owner_id is not _UNSCOPED and not _visible(row, owner_id):
                return None
            return self._to_view(row)

    def require(
        self,
        session_id: str,
        *,
        owner_id: Any = _UNSCOPED,
    ) -> dict[str, Any]:
        view = self.get(session_id, owner_id=owner_id)
        if view is None:
            raise SessionNotFoundError(session_id)
        return view

    def rename(
        self,
        session_id: str,
        title: str | None,
        *,
        owner_id: str | None = None,
    ) -> dict[str, Any]:
        with self._session_factory() as db:
            row = db.get(ConversationSessionRow, session_id)
            if row is None or not _visible(row, owner_id):
                raise SessionNotFoundError(session_id)
            cleaned = title.strip() if isinstance(title, str) else None
            row.title = cleaned or None
            row.updated_at = _utcnow()
            db.commit()
            db.refresh(row)
            return self._to_view(row)

    def delete(self, session_id: str, *, owner_id: str | None = None) -> None:
        with self._session_factory() as db:
            row = db.get(ConversationSessionRow, session_id)
            if row is None or not _visible(row, owner_id):
                raise SessionNotFoundError(session_id)
            db.delete(row)
            db.commit()

    def append_turn(
        self,
        session_id: str,
        *,
        question: str,
        answer: str | None,
        citations: list[dict[str, Any]] | None,
        status: str,
        thread_id: str | None = None,
        resolved_question: str | None = None,
        custom_notes: list[dict[str, Any]] | None = None,
        facts_update: ConversationFacts | None = None,
        new_anchors: list[Anchor] | None = None,
        owner_id: Any = _UNSCOPED,
    ) -> dict[str, Any]:
        if status not in {"completed", "rejected"}:
            raise ValueError(f"Cannot append non-terminal status: {status}")

        citation_snapshots: list[dict[str, Any]] = []
        for item in citations or []:
            citation_snapshots.append(
                {
                    "chunk_id": item.get("chunk_id"),
                    "document_id": item.get("document_id"),
                    "source_path": item.get("source_path") or "",
                    "document_type": item.get("document_type") or "",
                    "score": float(item.get("score") or 0.0),
                    "excerpt": (item.get("excerpt") or "")[:400],
                }
            )

        note_snapshots: list[dict[str, str]] = []
        for item in custom_notes or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            note = str(item.get("note") or "").strip()
            if key and note:
                note_snapshots.append({"key": key, "note": note[:2000]})

        turn: dict[str, Any] = {
            "question": question,
            "answer": answer,
            "citations": citation_snapshots,
            "custom_notes": note_snapshots,
            "status": status,
            "thread_id": thread_id,
            "created_at": _utcnow().isoformat(),
        }
        cleaned_resolved = (
            resolved_question.strip() if isinstance(resolved_question, str) else None
        )
        if cleaned_resolved and cleaned_resolved != question.strip():
            turn["resolved_question"] = cleaned_resolved

        with self._session_factory() as db:
            row = db.get(ConversationSessionRow, session_id)
            if row is None:
                raise SessionNotFoundError(session_id)
            if owner_id is not _UNSCOPED and not _visible(row, owner_id):
                raise SessionNotFoundError(session_id)
            history = list(row.history or [])
            history.append(turn)
            row.history = history
            if not row.title:
                row.title = _truncate_title(question)

            if facts_update is not None or new_anchors:
                bag = SessionMemory.from_dict(
                    row.memory if isinstance(row.memory, dict) else None
                )
                if facts_update is not None:
                    bag.facts = bag.facts.merge_with(facts_update)
                if new_anchors:
                    bag.anchors = merge_anchors(bag.anchors, list(new_anchors))
                row.memory = bag.to_dict()

            row.updated_at = _utcnow()
            db.commit()
            db.refresh(row)
            return self._to_view(row)

    @staticmethod
    def _to_view(row: ConversationSessionRow) -> dict[str, Any]:
        memory = SessionMemory.from_dict(
            row.memory if isinstance(getattr(row, "memory", None), dict) else None
        )
        return {
            "session_id": row.id,
            "title": row.title,
            "owner_id": row.owner_id,
            "history": list(row.history or []),
            "memory": memory.to_dict(),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
            "turn_count": len(row.history or []),
        }
