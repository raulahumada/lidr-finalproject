from __future__ import annotations

from pathlib import Path

from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.models import ChunkRow, DocumentRow
from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.constants import EMBEDDING_DIMENSIONS
from app.ingestion.orchestrator import run_ingest
from sqlalchemy import func, select


class _FakeEmbedder:
    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [[0.01 * (i + 1)] * EMBEDDING_DIMENSIONS for i, _ in enumerate(texts)]


def test_orchestrator_ingests_and_skips_existing(tmp_path: Path) -> None:
    (tmp_path / "doc.txt").write_text(
        "Metropol cobranzas handoff.\n\nSegundo parrafo ventas Tenela.",
        encoding="utf-8",
    )
    (tmp_path / "noise.xlsx").write_text("x", encoding="utf-8")
    store = ChunkStore()
    factory = get_session_factory()

    # Cleanup prior test docs with same relative path if any pollute DB
    with factory() as session:
        store.delete_document_by_source_path(session, "doc.txt")
        session.commit()

    summary = run_ingest(
        corpus_root=tmp_path,
        allowlist={"txt", "md"},
        session_factory=factory,
        embedder=_FakeEmbedder(),
        store=store,
        force=False,
    )
    assert summary.ingested == 1
    assert summary.skipped_extension >= 1
    assert summary.chunks >= 1

    again = run_ingest(
        corpus_root=tmp_path,
        allowlist={"txt", "md"},
        session_factory=factory,
        embedder=_FakeEmbedder(),
        store=store,
        force=False,
    )
    assert again.skipped_existing == 1
    assert again.ingested == 0

    with factory() as session:
        docs = session.execute(
            select(func.count()).select_from(DocumentRow).where(DocumentRow.source_path == "doc.txt")
        ).scalar_one()
        chunks = session.execute(
            select(func.count())
            .select_from(ChunkRow)
            .join(DocumentRow)
            .where(DocumentRow.source_path == "doc.txt")
        ).scalar_one()
        assert docs == 1
        assert chunks >= 1
        store.delete_document_by_source_path(session, "doc.txt")
        session.commit()
