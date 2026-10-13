"""Agent catalog + custom profile CRUD for the Metropol console."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.domain.graph.agent_store import (
    AgentConflictError,
    AgentImmutableError,
    AgentNotFoundError,
    AgentStore,
)
from app.domain.graph.catalog import agent_catalog, builtin_keys, get_agent_detail
from app.foundation.persistence.database import get_session_factory
from app.schemas.agent_profile import AgentProfile, AgentProfileCreate, AgentProfileUpdate

router = APIRouter(tags=["answer-agents"])


def _store() -> AgentStore:
    return AgentStore(get_session_factory())


@router.get("/answer/agents")
def list_answer_agents() -> dict[str, Any]:
    return agent_catalog()


@router.get("/answer/agents/{key}")
def get_answer_agent(key: str) -> dict[str, Any]:
    detail = get_agent_detail(key)
    if detail is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return detail


@router.post(
    "/answer/agents",
    status_code=status.HTTP_201_CREATED,
    response_model=AgentProfile,
)
def create_answer_agent(body: AgentProfileCreate) -> dict[str, Any]:
    try:
        created = _store().create(
            key=body.key,
            label=body.label,
            role=body.role,
            system_prompt=body.system_prompt,
            enabled=body.enabled,
            builtin_keys=builtin_keys(),
        )
    except AgentConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    created["mutable"] = True
    created["prompt_preview"] = created.get("system_prompt")
    return created


@router.patch("/answer/agents/{key}", response_model=AgentProfile)
def update_answer_agent(key: str, body: AgentProfileUpdate) -> dict[str, Any]:
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields to update",
        )
    try:
        updated = _store().update(key, builtin_keys=builtin_keys(), **data)
    except AgentImmutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=str(exc)
        ) from exc
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    updated["mutable"] = True
    updated["prompt_preview"] = updated.get("system_prompt")
    return updated


@router.delete("/answer/agents/{key}", status_code=status.HTTP_204_NO_CONTENT)
def delete_answer_agent(key: str) -> None:
    try:
        _store().delete(key, builtin_keys=builtin_keys())
    except AgentImmutableError as exc:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED, detail=str(exc)
        ) from exc
    except AgentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
        ) from exc
