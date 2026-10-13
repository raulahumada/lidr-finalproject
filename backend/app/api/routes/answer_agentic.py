"""Thin HTTP layer for agentic (LangGraph) answers + live progress."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.dependencies import get_activity_log, get_agentic_answer_runner
from app.domain.graph.activity import GraphActivityLog
from app.domain.graph.runner import AgenticAnswerRunner
from app.schemas.agentic_answer import (
    AgenticAnswerRequest,
    AgenticAnswerResponse,
    AgenticProgressResponse,
    AgenticResumeRequest,
    AgenticStartResponse,
    GraphActivityEntry,
)
from app.schemas.answer import Citation

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
    "/answer/agentic/start",
    response_model=AgenticStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def answer_agentic_start(
    request: AgenticAnswerRequest,
    runner: Optional[AgenticAnswerRunner] = Depends(get_agentic_answer_runner),
) -> AgenticStartResponse:
    if runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agentic answer is not available (missing OPENAI_API_KEY).",
        )
    try:
        thread_id = runner.start_background_run(
            question=request.question,
            k=request.k,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start agentic answer.",
        ) from exc
    return AgenticStartResponse(thread_id=thread_id)


@router.get(
    "/answer/agentic/{thread_id}/progress",
    response_model=AgenticProgressResponse,
)
def answer_agentic_progress(
    thread_id: str,
    activity_log: GraphActivityLog = Depends(get_activity_log),
) -> AgenticProgressResponse:
    run = activity_log.read(thread_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown or expired thread_id. Did you call POST /answer/agentic/start first?",
        )

    activity = [
        GraphActivityEntry(
            node=entry.node,
            label=entry.label,
            message=entry.message,
            at=entry.at,
        )
        for entry in run.entries
    ]

    if run.status in ("running", "failed"):
        return AgenticProgressResponse(
            status=run.status,
            thread_id=thread_id,
            activity=activity,
            question=run.question,
            error=run.error,
        )

    result = run.result or {}
    citations_raw = result.get("citations") or []
    citations: list[Citation] = []
    for item in citations_raw:
        try:
            citations.append(Citation.model_validate(item))
        except Exception:  # noqa: BLE001
            continue

    status_value = run.status
    if status_value not in {
        "completed",
        "awaiting_human_review",
        "failed",
        "rejected",
        "running",
    }:
        status_value = "completed"

    return AgenticProgressResponse(
        status=status_value,  # type: ignore[arg-type]
        thread_id=thread_id,
        activity=activity,
        question=result.get("question") or run.question,
        answer=result.get("answer"),
        citations=citations,
        agent_trace=result.get("agent_trace") or [],
        review_reasons=list(result.get("review_reasons") or []),
        confidence=result.get("confidence"),
        no_evidence=bool(result.get("no_evidence")),
        citations_valid=result.get("citations_valid"),
        prompt_version=result.get("prompt_version"),
        k=result.get("k"),
        interrupt_payload=result.get("interrupt_payload"),
        error=run.error,
    )


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
