"""HTTP contracts for agentic answer, progress, and human-gate resume."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.answer import Citation
from app.schemas.usage import TokenUsage


class RoutingHistoryEntry(BaseModel):
    step: int
    next_agent: str
    reason: str = ""
    source: str = ""


class AgenticAnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    k: int | None = Field(default=None, ge=1, le=50)
    session_id: str | None = Field(default=None, min_length=1, max_length=64)
    domain: str | None = Field(
        default=None,
        description="Metropol domain override, or omit/auto for detection.",
        max_length=32,
    )


class AgenticResumeRequest(BaseModel):
    decision: Literal["approve", "reject", "adjust"] = "approve"
    note: str | None = Field(default=None, max_length=2000)
    adjusted_answer: str | None = Field(default=None, max_length=8000)


class AgentTraceStep(BaseModel):
    node: str
    summary: str


class CustomAgentNote(BaseModel):
    key: str
    note: str


class AgenticAnswerResponse(BaseModel):
    status: Literal[
        "completed",
        "awaiting_human_review",
        "rejected",
    ]
    thread_id: str
    question: str
    resolved_question: str | None = None
    domain: str | None = None
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    agent_trace: list[AgentTraceStep] = Field(default_factory=list)
    routing_history: list[RoutingHistoryEntry] = Field(default_factory=list)
    custom_notes: list[CustomAgentNote] = Field(default_factory=list)
    review_reasons: list[str] = Field(default_factory=list)
    confidence: float | None = None
    no_evidence: bool = False
    citations_valid: bool | None = None
    prompt_version: str | None = None
    k: int | None = None
    interrupt_payload: dict[str, Any] | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)


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
    resolved_question: str | None = None
    domain: str | None = None
    answer: str | None = None
    citations: list[Citation] = Field(default_factory=list)
    agent_trace: list[AgentTraceStep] = Field(default_factory=list)
    routing_history: list[RoutingHistoryEntry] = Field(default_factory=list)
    custom_notes: list[CustomAgentNote] = Field(default_factory=list)
    review_reasons: list[str] = Field(default_factory=list)
    confidence: float | None = None
    no_evidence: bool = False
    citations_valid: bool | None = None
    prompt_version: str | None = None
    k: int | None = None
    interrupt_payload: dict[str, Any] | None = None
    error: str | None = None
    usage: TokenUsage = Field(default_factory=TokenUsage)
