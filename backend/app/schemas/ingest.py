"""HTTP contracts for corpus ingest runs and stats."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

IngestRunStatus = Literal["queued", "running", "completed", "failed"]


class IngestRunRequest(BaseModel):
    force: bool = False


class IngestRunStartResponse(BaseModel):
    run_id: str
    status: Literal["queued", "running"]


class IngestSummaryView(BaseModel):
    seen: int = 0
    ingested: int = 0
    skipped_extension: int = 0
    skipped_existing: int = 0
    failed: int = 0
    chunks: int = 0
    errors: list[str] = Field(default_factory=list)


class IngestRunStatusResponse(BaseModel):
    run_id: str
    status: IngestRunStatus
    force: bool = False
    summary: IngestSummaryView | None = None
    error: str | None = None


class IngestStatsResponse(BaseModel):
    document_count: int
    chunk_count: int
    corpus_root: str
    allowlist: list[str]
