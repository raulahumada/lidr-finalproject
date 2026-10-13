from __future__ import annotations

import pytest

from app.config import get_settings
from app.foundation.persistence.database import get_session_factory
from app.generation.conversation.store import SessionNotFoundError, SessionStore


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
def test_store_create_append_and_auto_title() -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    get_session_factory.cache_clear()
    store = SessionStore(get_session_factory())
    created = store.create()
    session_id = created["session_id"]

    store.append_turn(
        session_id,
        question="¿Cómo es el handoff de cobranzas con Tenela?",
        answer="Respuesta de prueba",
        citations=[],
        status="completed",
        thread_id="abc123",
        custom_notes=[{"key": "risk_advisor", "note": "cuidado con mora"}],
    )
    view = store.require(session_id)
    assert view["title"]
    assert len(view["history"]) == 1
    assert view["history"][0]["status"] == "completed"
    assert view["history"][0]["custom_notes"][0]["key"] == "risk_advisor"

    store.append_turn(
        session_id,
        question="otra",
        answer=None,
        citations=[],
        status="rejected",
        thread_id="def456",
    )
    view2 = store.require(session_id)
    assert len(view2["history"]) == 2
    assert view2["history"][1]["status"] == "rejected"

    with pytest.raises(ValueError):
        store.append_turn(
            session_id,
            question="x",
            answer=None,
            citations=[],
            status="awaiting_human_review",
        )

    with pytest.raises(SessionNotFoundError):
        store.require("missing-session")

    store.delete(session_id)


@pytest.mark.integration
def test_store_owner_isolation() -> None:
    if not _postgres_available():
        pytest.skip("DATABASE_URL not reachable")

    get_session_factory.cache_clear()
    store = SessionStore(get_session_factory())
    a = store.create(owner_id="user-a")["session_id"]
    b = store.create(owner_id="user-b")["session_id"]
    orphan = store.create()["session_id"]

    a_ids = {item["session_id"] for item in store.list_summaries(owner_id="user-a")}
    assert a in a_ids
    assert b not in a_ids
    assert orphan not in a_ids

    assert store.get(a, owner_id="user-b") is None
    assert store.get(a, owner_id="user-a") is not None
    assert store.get(orphan, owner_id="user-a") is None
    assert store.get(orphan, owner_id=None) is not None

    with pytest.raises(SessionNotFoundError):
        store.delete(a, owner_id="user-b")

    store.delete(a, owner_id="user-a")
    store.delete(b, owner_id="user-b")
    store.delete(orphan, owner_id=None)
