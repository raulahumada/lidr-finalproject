"""Walk → parse → chunk → embed → persist."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from sqlalchemy.orm import sessionmaker

from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.chunking import chunk_document
from app.ingestion.loaders import iter_corpus_files
from app.ingestion.parsers.registry import ParserRegistry, default_registry


class Embedder(Protocol):
    def embed_many(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class IngestSummary:
    seen: int = 0
    ingested: int = 0
    skipped_extension: int = 0
    skipped_existing: int = 0
    failed: int = 0
    chunks: int = 0
    errors: list[str] = field(default_factory=list)


def run_ingest(
    *,
    corpus_root: Path,
    allowlist: set[str],
    session_factory: sessionmaker,
    embedder: Embedder,
    store: ChunkStore | None = None,
    registry: ParserRegistry | None = None,
    force: bool = False,
) -> IngestSummary:
    if not corpus_root.is_dir():
        raise FileNotFoundError(f"CORPUS_ROOT is not a directory: {corpus_root}")

    store = store or ChunkStore()
    registry = registry or default_registry()
    summary = IngestSummary()

    for corpus_file, absolute in iter_corpus_files(corpus_root, allowlist=allowlist):
        summary.seen += 1
        if corpus_file is None:
            summary.skipped_extension += 1
            continue

        source_path = corpus_file.relative_path
        try:
            with session_factory() as session:
                existing_id = store.find_document_id(session, source_path)
                if existing_id is not None and not force:
                    summary.skipped_existing += 1
                    continue
                if existing_id is not None and force:
                    store.delete_document_by_source_path(session, source_path)
                    session.commit()

            text = registry.get(corpus_file.extension).parse(corpus_file.absolute_path)
            pieces = chunk_document(text, extension=corpus_file.extension)
            if not pieces:
                summary.failed += 1
                summary.errors.append(f"{source_path}: no extractable text")
                continue

            vectors = embedder.embed_many([p.content for p in pieces])
            chunk_rows = [
                (
                    piece.strategy,
                    piece.content,
                    vector,
                    {
                        "index": index,
                        "strategy": piece.strategy,
                        **({"section": piece.section} if piece.section else {}),
                    },
                )
                for index, (piece, vector) in enumerate(zip(pieces, vectors))
            ]

            with session_factory() as session:
                store.persist_document_with_chunks(
                    session,
                    source_path=source_path,
                    document_type=corpus_file.extension,
                    doc_metadata={"corpus": "metropol"},
                    chunks=chunk_rows,
                )
                session.commit()

            summary.ingested += 1
            summary.chunks += len(chunk_rows)
        except Exception as exc:  # noqa: BLE001 — per-file isolation for batch runs
            summary.failed += 1
            summary.errors.append(f"{source_path}: {type(exc).__name__}: {exc}")

    return summary
