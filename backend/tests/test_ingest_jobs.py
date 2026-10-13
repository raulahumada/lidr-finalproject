"""Unit tests for in-process ingest job registry (no OpenAI)."""

from __future__ import annotations

import pytest

from app.ingestion.jobs import IngestBusyError, IngestJobRegistry
from app.ingestion.orchestrator import IngestSummary


def test_create_and_get() -> None:
    registry = IngestJobRegistry()
    job = registry.create(force=True)
    assert job.status == "queued"
    assert job.force is True
    fetched = registry.get(job.run_id)
    assert fetched is not None
    assert fetched.run_id == job.run_id


def test_busy_rejects_second_create() -> None:
    registry = IngestJobRegistry()
    first = registry.create()
    with pytest.raises(IngestBusyError):
        registry.create()
    registry.mark_running(first.run_id)
    with pytest.raises(IngestBusyError):
        registry.create()
    registry.complete(first.run_id, IngestSummary(seen=1, ingested=1, chunks=1))
    second = registry.create()
    assert second.run_id != first.run_id


def test_complete_and_fail() -> None:
    registry = IngestJobRegistry()
    job = registry.create()
    registry.mark_running(job.run_id)
    summary = IngestSummary(seen=3, ingested=2, failed=1, chunks=4, errors=["a.txt: boom"])
    registry.complete(job.run_id, summary)
    done = registry.get(job.run_id)
    assert done is not None
    assert done.status == "completed"
    assert done.summary is not None
    assert done.summary.ingested == 2
    assert done.errors == ["a.txt: boom"]

    other = registry.create()
    registry.fail(other.run_id, "explode")
    failed = registry.get(other.run_id)
    assert failed is not None
    assert failed.status == "failed"
    assert failed.error == "explode"
