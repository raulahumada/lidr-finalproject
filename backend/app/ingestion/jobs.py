"""In-process registry for HTTP ingest runs (single concurrent run).

Mirrors the agentic GraphActivityLog pattern: fine for one-worker local
Uvicorn; state is lost on reload.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from typing import Literal

from app.ingestion.orchestrator import IngestSummary

IngestJobStatus = Literal["queued", "running", "completed", "failed"]

_MAX_ERRORS = 50


class IngestBusyError(Exception):
    """Raised when a create is attempted while another run is active."""


@dataclass
class IngestJob:
    run_id: str
    status: IngestJobStatus = "queued"
    force: bool = False
    summary: IngestSummary | None = None
    error: str | None = None
    errors: list[str] = field(default_factory=list)


class IngestJobRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, IngestJob] = {}

    def has_active(self) -> bool:
        with self._lock:
            return any(j.status in ("queued", "running") for j in self._jobs.values())

    def create(self, *, force: bool = False) -> IngestJob:
        with self._lock:
            if any(j.status in ("queued", "running") for j in self._jobs.values()):
                raise IngestBusyError("An ingest run is already in progress")
            run_id = str(uuid.uuid4())
            job = IngestJob(run_id=run_id, force=force)
            self._jobs[run_id] = job
            return job

    def mark_running(self, run_id: str) -> None:
        with self._lock:
            job = self._jobs.get(run_id)
            if job is None:
                return
            job.status = "running"

    def complete(self, run_id: str, summary: IngestSummary) -> None:
        with self._lock:
            job = self._jobs.get(run_id)
            if job is None:
                return
            job.status = "completed"
            job.summary = summary
            job.errors = list(summary.errors[:_MAX_ERRORS])
            job.error = None

    def fail(self, run_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs.get(run_id)
            if job is None:
                return
            job.status = "failed"
            job.error = message[:800]
            job.summary = None

    def get(self, run_id: str) -> IngestJob | None:
        with self._lock:
            return self._jobs.get(run_id)

    def clear(self) -> None:
        """Test helper — drop all jobs."""
        with self._lock:
            self._jobs.clear()
