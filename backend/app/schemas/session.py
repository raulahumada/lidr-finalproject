from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SessionCreated(BaseModel):
    session_id: str


class SessionSummary(BaseModel):
    session_id: str
    title: str | None = None
    created_at: datetime
    updated_at: datetime
    turn_count: int = 0


class HistoryTurnCitation(BaseModel):
    chunk_id: int | None = None
    document_id: int | None = None
    source_path: str = ""
    document_type: str = ""
    score: float = 0.0
    excerpt: str = ""


class HistoryTurn(BaseModel):
    question: str
    resolved_question: str | None = None
    answer: str | None = None
    citations: list[HistoryTurnCitation] = Field(default_factory=list)
    status: Literal["completed", "rejected"] = "completed"
    thread_id: str | None = None
    created_at: str | datetime


class SessionView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    title: str | None = None
    history: list[HistoryTurn] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    turn_count: int = 0


class SessionUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
