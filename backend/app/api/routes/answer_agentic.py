"""Thin HTTP layer for agentic (LangGraph) answers."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_agentic_answer_runner
from app.domain.graph.runner import AgenticAnswerRunner
from app.schemas.agentic_answer import (
    AgenticAnswerRequest,
    AgenticAnswerResponse,
    AgenticResumeRequest,
)

router = APIRouter(tags=["answer-agentic"])


@router.post(
    "/answer/agentic",
    response_model=AgenticAnswerResponse,
    responses={202: {"model": AgenticAnswerResponse}},
)
def answer_agentic(
    request: AgenticAnswerRequest,
    response: Response,
    runner: Optional[AgenticAnswerRunner] = Depends(get_agentic_answer_runner),
) -> AgenticAnswerResponse:
    if runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agentic answer is not available (missing OPENAI_API_KEY).",
        )
    try:
        result = runner.start(question=request.question, k=request.k)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run agentic answer.",
        ) from exc
    if result.status == "awaiting_human_review":
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.post(
    "/answer/agentic/{thread_id}/resume",
    response_model=AgenticAnswerResponse,
)
def resume_agentic(
    thread_id: str,
    request: AgenticResumeRequest,
    runner: Optional[AgenticAnswerRunner] = Depends(get_agentic_answer_runner),
) -> AgenticAnswerResponse:
    if runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agentic answer is not available (missing OPENAI_API_KEY).",
        )
    try:
        return runner.resume(
            thread_id=thread_id,
            decision=request.decision,
            note=request.note,
            adjusted_answer=request.adjusted_answer,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown or not-paused agentic thread.",
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resume agentic answer.",
        ) from exc
