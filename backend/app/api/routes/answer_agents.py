"""Agent catalog for the Metropol console."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.domain.graph.catalog import agent_catalog

router = APIRouter(tags=["answer-agents"])


@router.get("/answer/agents")
def list_answer_agents() -> dict[str, Any]:
    return agent_catalog()
