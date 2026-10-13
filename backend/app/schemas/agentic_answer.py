from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.answer import Citation


class AgenticAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    k: int | None = Field(default=None, ge=1, le=50)


class AgenticResumeRequest(BaseModel):
    decision: Literal["approve", "reject", "adjust"] = "approve"
    note: str | None = Field(default=None, max_length=2000)
    adjusted_answer: str | None = Field(default=None, max_length=8000)


class AgentTraceStep(BaseModel):
    node: str
    summary: str


class AgenticAnswerResponse(BaseModel):
    status: Literal[
        "completed",
        "awaiting_human_review",
        "rejected",
    ]
    thread_id: str
    question: str
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    agent_trace: list[AgentTraceStep] = Field(default_factory=list)
    review_reasons: list[str] = Field(default_factory=list)
    confidence: float | None = None
    no_evidence: bool = False
    citations_valid: bool | None = None
    prompt_version: str | None = None
    k: int | None = None
    interrupt_payload: dict[str, Any] | None = None


class AgenticStartResponse(BaseModel):
    status: Literal["running"] = "running"
    thread_id: str


class GraphActivityEntry(BaseModel):
    node: str
    label: str
    message: str
    at: float


class AgenticProgressResponse(BaseModel):
    status: Literal[
        "running",
        "completed",
        "awaiting_human_review",
        "failed",
        "rejected",
    ]
    thread_id: str
    activity: list[GraphActivityEntry] = Field(default_factory=list)
    question: str | None = None
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    agent_trace: list[AgentTraceStep] = Field(default_factory=list)
    review_reasons: list[str] = Field(default_factory=list)
    confidence: float | None = None
    no_evidence: bool = False
    citations_valid: bool | None = None
    prompt_version: str | None = None
    k: int | None = None
    interrupt_payload: dict[str, Any] | None = None
    error: str | None = None
