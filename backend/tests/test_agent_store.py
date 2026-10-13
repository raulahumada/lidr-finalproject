from __future__ import annotations

import pytest

from app.config import get_settings
from app.domain.graph.agent_store import (
    AgentConflictError,
    AgentImmutableError,
    AgentNotFoundError,
    AgentStore,
    validate_custom_key,
)
from app.domain.graph.catalog import builtin_keys
from app.foundation.persistence.database import get_session_factory


def test_validate_custom_key_rejects_builtin() -> None:
    with pytest.raises(AgentConflictError):
        validate_custom_key("corpus_fetcher", builtin_keys=builtin_keys())


def test_validate_custom_key_ok() -> None:
    assert validate_custom_key("risk_advisor", builtin_keys=builtin_keys()) == "risk_advisor"


def _postgres_available() -> bool:
    settings = get_settings()
    if not settings.database_url.strip():
        return False
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return True
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.integration
def test_agent_store_crud_roundtrip() -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    get_session_factory.cache_clear()
    store = AgentStore(get_session_factory())
    key = "test_risk_advisor"
    try:
        store.delete(key, builtin_keys=builtin_keys())
    except AgentNotFoundError:
        pass

    created = store.create(
        key=key,
        label="Risk advisor",
        role="Señala riesgos",
        system_prompt="Sos un asesor de riesgo breve.",
        enabled=True,
        builtin_keys=builtin_keys(),
    )
    assert created["key"] == key
    assert key in store.list_enabled_keys()

    updated = store.update(
        key,
        builtin_keys=builtin_keys(),
        label="Risk advisor v2",
        enabled=False,
    )
    assert updated["label"] == "Risk advisor v2"
    assert key not in store.list_enabled_keys()

    with pytest.raises(AgentImmutableError):
        store.update("orchestrator", builtin_keys=builtin_keys(), label="x")

    store.delete(key, builtin_keys=builtin_keys())
    assert store.get(key) is None
