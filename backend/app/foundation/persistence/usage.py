"""Durable ledger of chat-completion token usage.

Writes happen at ``complete_json`` success — a later human-review reject does
not un-bill the provider. ``record`` uses its own short-lived sync session.

|| Ledger durable del uso de tokens de chat.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.foundation.llm.usage import Usage
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.models import LlmUsageEventRow


@dataclass(frozen=True)
class UsageByModel:
    model: str
    calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class UsageTotals:
    total_calls: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    by_model: list[UsageByModel]


class UsageStore:
    """Insert one event; aggregate many."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] | sessionmaker[Session] | None = None,
    ) -> None:
        self._session_factory = session_factory

    def _factory(self) -> sessionmaker[Session] | Callable[[], Session]:
        return self._session_factory or get_session_factory()

    def record(
        self,
        *,
        purpose: str,
        model: str,
        usage: Usage,
        session_id: str | None = None,
        thread_id: str | None = None,
        owner_id: str | None = None,
    ) -> None:
        """Insert one row and commit (own transaction)."""
        row = LlmUsageEventRow(
            id=str(uuid4()),
            purpose=purpose,
            model=model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            reported=usage.reported,
            session_id=session_id,
            thread_id=thread_id,
            owner_id=owner_id,
        )
        factory = self._factory()
        with factory() as session:
            session.add(row)
            session.commit()

    def summarize(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        session_id: str | None = None,
        purpose: str | None = None,
    ) -> UsageTotals:
        """Aggregate the ledger. Empty window → zeros, not an error."""
        filters = []
        if since is not None:
            filters.append(LlmUsageEventRow.created_at >= since)
        if until is not None:
            filters.append(LlmUsageEventRow.created_at <= until)
        if session_id is not None:
            filters.append(LlmUsageEventRow.session_id == session_id)
        if purpose is not None:
            filters.append(LlmUsageEventRow.purpose == purpose)

        stmt = (
            select(
                LlmUsageEventRow.model,
                func.count().label("calls"),
                func.coalesce(func.sum(LlmUsageEventRow.input_tokens), 0).label(
                    "input_tokens"
                ),
                func.coalesce(func.sum(LlmUsageEventRow.output_tokens), 0).label(
                    "output_tokens"
                ),
                func.coalesce(func.sum(LlmUsageEventRow.total_tokens), 0).label(
                    "total_tokens"
                ),
            )
            .group_by(LlmUsageEventRow.model)
            .order_by(LlmUsageEventRow.model)
        )
        if filters:
            stmt = stmt.where(*filters)

        factory = self._factory()
        with factory() as session:
            rows = session.execute(stmt).all()

        by_model = [
            UsageByModel(
                model=str(row.model),
                calls=int(row.calls),
                input_tokens=int(row.input_tokens),
                output_tokens=int(row.output_tokens),
                total_tokens=int(row.total_tokens),
            )
            for row in rows
        ]
        return UsageTotals(
            total_calls=sum(item.calls for item in by_model),
            input_tokens=sum(item.input_tokens for item in by_model),
            output_tokens=sum(item.output_tokens for item in by_model),
            total_tokens=sum(item.total_tokens for item in by_model),
            by_model=by_model,
        )
