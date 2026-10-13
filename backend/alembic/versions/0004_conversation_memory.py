"""Add memory JSONB bag (facts + anchors) on conversation sessions.

Revision ID: 0004_conversation_memory
Revises: 0003_agent_profiles
Create Date: 2026-10-13
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_conversation_memory"
down_revision: Union[str, None] = "0003_agent_profiles"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conversation_sessions",
        sa.Column(
            "memory",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("conversation_sessions", "memory")
