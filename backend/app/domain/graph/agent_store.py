"""CRUD for custom agent profiles (builtins are not stored here)."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.foundation.persistence.models import AgentProfileRow

_KEY_RE = re.compile(r"^[a-z][a-z0-9_]{1,62}$")


class AgentStoreError(Exception):
    """Base error for agent profile operations."""


class AgentConflictError(AgentStoreError):
    """Key already exists or is reserved for a builtin."""


class AgentNotFoundError(AgentStoreError):
    """Custom profile key missing."""


class AgentImmutableError(AgentStoreError):
    """Attempt to mutate a builtin key."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_custom_key(key: str, *, builtin_keys: set[str]) -> str:
    cleaned = (key or "").strip().lower()
    if not _KEY_RE.match(cleaned):
        raise ValueError(
            "key must be snake_case starting with a letter (2–63 chars)"
        )
    if cleaned in builtin_keys:
        raise AgentConflictError(f"key {cleaned!r} is reserved for a builtin agent")
    return cleaned


class AgentStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_customs(self) -> list[dict[str, Any]]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(AgentProfileRow).order_by(AgentProfileRow.key.asc())
            ).all()
            return [self._to_dict(row) for row in rows]

    def list_enabled_keys(self) -> list[str]:
        with self._session_factory() as db:
            rows = db.scalars(
                select(AgentProfileRow)
                .where(AgentProfileRow.enabled.is_(True))
                .order_by(AgentProfileRow.key.asc())
            ).all()
            return [row.key for row in rows]

    def get(self, key: str) -> dict[str, Any] | None:
        with self._session_factory() as db:
            row = db.get(AgentProfileRow, key)
            if row is None:
                return None
            return self._to_dict(row)

    def get_system_prompt(self, key: str) -> str | None:
        with self._session_factory() as db:
            row = db.get(AgentProfileRow, key)
            if row is None or not row.enabled:
                return None
            return row.system_prompt

    def create(
        self,
        *,
        key: str,
        label: str,
        role: str,
        system_prompt: str,
        enabled: bool = True,
        builtin_keys: set[str],
    ) -> dict[str, Any]:
        cleaned = validate_custom_key(key, builtin_keys=builtin_keys)
        label_c = label.strip()
        role_c = role.strip()
        prompt_c = system_prompt.strip()
        if not label_c or not role_c or not prompt_c:
            raise ValueError("label, role, and system_prompt are required")

        now = _utcnow()
        with self._session_factory() as db:
            if db.get(AgentProfileRow, cleaned) is not None:
                raise AgentConflictError(f"key {cleaned!r} already exists")
            row = AgentProfileRow(
                key=cleaned,
                label=label_c,
                role=role_c,
                system_prompt=prompt_c,
                enabled=enabled,
                created_at=now,
                updated_at=now,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def update(
        self,
        key: str,
        *,
        builtin_keys: set[str],
        label: str | None = None,
        role: str | None = None,
        system_prompt: str | None = None,
        enabled: bool | None = None,
    ) -> dict[str, Any]:
        if key in builtin_keys:
            raise AgentImmutableError(f"builtin agent {key!r} is not mutable")
        with self._session_factory() as db:
            row = db.get(AgentProfileRow, key)
            if row is None:
                raise AgentNotFoundError(key)
            if label is not None:
                cleaned = label.strip()
                if not cleaned:
                    raise ValueError("label cannot be empty")
                row.label = cleaned
            if role is not None:
                cleaned = role.strip()
                if not cleaned:
                    raise ValueError("role cannot be empty")
                row.role = cleaned
            if system_prompt is not None:
                cleaned = system_prompt.strip()
                if not cleaned:
                    raise ValueError("system_prompt cannot be empty")
                row.system_prompt = cleaned
            if enabled is not None:
                row.enabled = enabled
            row.updated_at = _utcnow()
            db.commit()
            db.refresh(row)
            return self._to_dict(row)

    def delete(self, key: str, *, builtin_keys: set[str]) -> None:
        if key in builtin_keys:
            raise AgentImmutableError(f"builtin agent {key!r} is not mutable")
        with self._session_factory() as db:
            row = db.get(AgentProfileRow, key)
            if row is None:
                raise AgentNotFoundError(key)
            db.delete(row)
            db.commit()

    @staticmethod
    def _to_dict(row: AgentProfileRow) -> dict[str, Any]:
        return {
            "key": row.key,
            "label": row.label,
            "role": row.role,
            "system_prompt": row.system_prompt,
            "enabled": bool(row.enabled),
            "kind": "custom",
            "llm_driven": True,
            "tools": [],
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }
