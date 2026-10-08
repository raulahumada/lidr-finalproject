"""Thin HTTP layer for grounded answers."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_answer_service
from app.domain.answer_service import AnswerService
from app.schemas.answer import AnswerRequest, AnswerResponse

router = APIRouter(tags=["answer"])


@router.post("/answer", response_model=AnswerResponse)
def answer(
    request: AnswerRequest,
    service: Optional[AnswerService] = Depends(get_answer_service),
) -> AnswerResponse:
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Answer service is not available (missing OPENAI_API_KEY).",
        )
    try:
        return service.answer(question=request.question, k=request.k)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate answer.",
        ) from exc
