"""Add owner_id for console-scoped conversation sessions.

Revision ID: 0005_session_owner_id
Revises: 0004_conversation_memory
Create Date: 2026-10-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_session_owner_id"
down_revision: Union[str, None] = "0004_conversation_memory"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_sessions",
        sa.Column("owner_id", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_conversation_sessions_owner_id_updated_at",
        "conversation_sessions",
        ["owner_id", "updated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_sessions_owner_id_updated_at",
        table_name="conversation_sessions",
    )
    op.drop_column("conversation_sessions", "owner_id")
