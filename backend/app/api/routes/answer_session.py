"""Thin HTTP layer for conversation sessions (transcript CRUD)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_session_store
from app.generation.conversation.store import SessionNotFoundError, SessionStore
from app.schemas.session import (
    SessionCreated,
    SessionSummary,
    SessionUpdate,
    SessionView,
)

router = APIRouter(prefix="/answer/session", tags=["answer-session"])
list_router = APIRouter(prefix="/answer/sessions", tags=["answer-session"])


def _view(raw: dict) -> SessionView:
    return SessionView.model_validate(raw)


@router.post("", response_model=SessionCreated, status_code=status.HTTP_201_CREATED)
def create_session(
    store: SessionStore = Depends(get_session_store),
) -> SessionCreated:
    view = store.create()
    return SessionCreated(session_id=view["session_id"])


@list_router.get("", response_model=list[SessionSummary])
def list_sessions(
    store: SessionStore = Depends(get_session_store),
) -> list[SessionSummary]:
    return [SessionSummary.model_validate(item) for item in store.list_summaries()]


@router.get("/{session_id}", response_model=SessionView)
def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> SessionView:
    view = store.get(session_id)
    if view is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown or deleted session_id.",
        )
    return _view(view)


@router.patch("/{session_id}", response_model=SessionView)
def rename_session(
    session_id: str,
    body: SessionUpdate,
    store: SessionStore = Depends(get_session_store),
) -> SessionView:
    try:
        return _view(store.rename(session_id, body.title))
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown or deleted session_id.",
        ) from exc


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> None:
    try:
        store.delete(session_id)
    except SessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown or deleted session_id.",
        ) from exc
