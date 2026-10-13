"""Thin HTTP layer for Metropol corpus ingest (start / poll / stats)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from openai import OpenAI

from app.config import Settings, get_settings
from app.dependencies import get_chunk_store, get_ingest_job_registry
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.embedder import OpenAIEmbedder
from app.ingestion.jobs import IngestBusyError, IngestJobRegistry
from app.ingestion.orchestrator import IngestSummary, run_ingest
from app.schemas.ingest import (
    IngestRunRequest,
    IngestRunStartResponse,
    IngestRunStatusResponse,
    IngestStatsResponse,
    IngestSummaryView,
)

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _summary_view(summary: IngestSummary, *, errors: list[str] | None = None) -> IngestSummaryView:
    return IngestSummaryView(
        seen=summary.seen,
        ingested=summary.ingested,
        skipped_extension=summary.skipped_extension,
        skipped_existing=summary.skipped_existing,
        failed=summary.failed,
        chunks=summary.chunks,
        errors=list(errors if errors is not None else summary.errors),
    )


def _require_ingest_ready(settings: Settings) -> Path:
    root_value = (settings.corpus_root or "").strip()
    if not root_value:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CORPUS_ROOT is not configured.",
        )
    if not settings.embeddings_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service is not available.",
        )
    if not (settings.database_url or "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured.",
        )
    corpus_root = Path(root_value).expanduser()
    if not corpus_root.is_dir():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"CORPUS_ROOT is not a directory: {corpus_root}",
        )
    return corpus_root


def _execute_ingest_run(
    *,
    run_id: str,
    force: bool,
    corpus_root: Path,
    allowlist: set[str],
    settings: Settings,
    registry: IngestJobRegistry,
    store: ChunkStore,
) -> None:
    registry.mark_running(run_id)
    try:
        embedder = OpenAIEmbedder(
            client=OpenAI(api_key=settings.openai_api_key),
            model=settings.embedding_model,
        )
        summary = run_ingest(
            corpus_root=corpus_root,
            allowlist=allowlist,
            session_factory=get_session_factory(),
            embedder=embedder,
            store=store,
            force=force,
        )
        registry.complete(run_id, summary)
    except Exception as exc:  # noqa: BLE001 — surface on poll
        registry.fail(run_id, f"{type(exc).__name__}: {exc}")


@router.post(
    "/runs",
    response_model=IngestRunStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def start_ingest_run(
    background: BackgroundTasks,
    request: IngestRunRequest | None = None,
    settings: Settings = Depends(get_settings),
    registry: IngestJobRegistry = Depends(get_ingest_job_registry),
    store: ChunkStore = Depends(get_chunk_store),
) -> IngestRunStartResponse:
    body = request or IngestRunRequest()
    corpus_root = _require_ingest_ready(settings)
    allowlist = set(settings.corpus_extensions_list)
    try:
        job = registry.create(force=body.force)
    except IngestBusyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    background.add_task(
        _execute_ingest_run,
        run_id=job.run_id,
        force=body.force,
        corpus_root=corpus_root,
        allowlist=allowlist,
        settings=settings,
        registry=registry,
        store=store,
    )
    return IngestRunStartResponse(run_id=job.run_id, status="queued")


@router.get("/runs/{run_id}", response_model=IngestRunStatusResponse)
def get_ingest_run(
    run_id: str,
    registry: IngestJobRegistry = Depends(get_ingest_job_registry),
) -> IngestRunStatusResponse:
    job = registry.get(run_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingest run not found.",
        )
    summary = None
    if job.summary is not None:
        summary = _summary_view(job.summary, errors=job.errors)
    return IngestRunStatusResponse(
        run_id=job.run_id,
        status=job.status,
        force=job.force,
        summary=summary,
        error=job.error,
    )


@router.get("/stats", response_model=IngestStatsResponse)
def get_ingest_stats(
    settings: Settings = Depends(get_settings),
    store: ChunkStore = Depends(get_chunk_store),
) -> IngestStatsResponse:
    if not (settings.database_url or "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DATABASE_URL is not configured.",
        )
    with get_session_factory()() as session:
        counts = store.count_corpus(session)
    return IngestStatsResponse(
        document_count=counts.document_count,
        chunk_count=counts.chunk_count,
        corpus_root=(settings.corpus_root or "").strip(),
        allowlist=list(settings.corpus_extensions_list),
    )
