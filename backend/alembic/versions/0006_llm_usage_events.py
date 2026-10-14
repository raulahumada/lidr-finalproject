"""Add llm_usage_events ledger for chat token accounting.

Revision ID: 0006_llm_usage_events
Revises: 0005_session_owner_id
Create Date: 2026-10-14
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_llm_usage_events"
down_revision: Union[str, None] = "0005_session_owner_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_usage_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("reported", sa.Boolean(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=True),
        sa.Column("thread_id", sa.String(length=64), nullable=True),
        sa.Column("owner_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_llm_usage_events_created_at", "llm_usage_events", ["created_at"]
    )
    op.create_index(
        "ix_llm_usage_events_session_id", "llm_usage_events", ["session_id"]
    )
    op.create_index("ix_llm_usage_events_purpose", "llm_usage_events", ["purpose"])


def downgrade() -> None:
    op.drop_index("ix_llm_usage_events_purpose", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_session_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_events_created_at", table_name="llm_usage_events")
    op.drop_table("llm_usage_events")
