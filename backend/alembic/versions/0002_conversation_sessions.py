"""Conversation sessions for durable chat transcripts.

Revision ID: 0002_conversation_sessions
Revises: 0001_rag_documents_chunks
Create Date: 2026-10-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_conversation_sessions"
down_revision: Union[str, None] = "0001_rag_documents_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "conversation_sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column(
            "history",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_conversation_sessions_updated_at",
        "conversation_sessions",
        ["updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_sessions_updated_at",
        table_name="conversation_sessions",
    )
    op.drop_table("conversation_sessions")
