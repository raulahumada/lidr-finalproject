from typing import Any, Literal

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)
    k: int | None = Field(default=None, ge=1, le=50)


class Citation(BaseModel):
    chunk_id: int
    document_id: int
    source_path: str
    document_type: str
    score: float
    excerpt: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnswerResponse(BaseModel):
    question: str
    answer: str
    citations: list[Citation]
    cached: Literal["exact", "semantic", "false"]
    prompt_version: str
    k: int
    latency_ms: int
    no_evidence: bool = False
