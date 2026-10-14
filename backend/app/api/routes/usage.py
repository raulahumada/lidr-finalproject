"""GET /usage/summary — chat-completion token aggregates.

Thin transport: the store aggregates. No USD.

|| GET /usage/summary — agregados de tokens de chat.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_usage_store
from app.foundation.persistence.usage import UsageStore
from app.schemas.usage import UsageByModel, UsageSummaryResponse

router = APIRouter(prefix="/usage", tags=["usage"])

UsagePurposeQuery = Literal["answer", "grounded_composer", "prompt_specialist"]


@router.get("/summary", response_model=UsageSummaryResponse)
def usage_summary(
    store: UsageStore = Depends(get_usage_store),
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    session_id: str | None = None,
    purpose: UsagePurposeQuery | None = None,
) -> UsageSummaryResponse:
    if since is not None and until is not None and since > until:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`from` must not be later than `to`.",
        )
    totals = store.summarize(
        since=since,
        until=until,
        session_id=session_id,
        purpose=purpose,
    )
    return UsageSummaryResponse(
        total_calls=totals.total_calls,
        input_tokens=totals.input_tokens,
        output_tokens=totals.output_tokens,
        total_tokens=totals.total_tokens,
        by_model=[
            UsageByModel(
                model=item.model,
                calls=item.calls,
                input_tokens=item.input_tokens,
                output_tokens=item.output_tokens,
                total_tokens=item.total_tokens,
            )
            for item in totals.by_model
        ],
    )
