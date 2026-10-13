"""Alembic environment — URL from Settings.database_url (not alembic.ini)."""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from pgvector.sqlalchemy import Vector
from sqlalchemy import engine_from_config, pool
from sqlalchemy.dialects.postgresql.base import ischema_names

from app.config import get_settings
from app.domain.graph.checkpointer import is_langgraph_checkpoint_table
from app.foundation.persistence.models import Base  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().database_url)

# Teach reflection about the vector column type for autogenerate/check.
ischema_names["vector"] = Vector

target_metadata = Base.metadata


def include_object(object, name, type_, reflected, compare_to):  # noqa: ANN001, A002
    """Skip LangGraph checkpointer tables (created by PostgresSaver.setup())."""
    if type_ == "table" and is_langgraph_checkpoint_table(name):
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
