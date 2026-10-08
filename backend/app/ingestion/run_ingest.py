"""CLI: ingest Metropol corpus into pgvector.

Usage (from backend/):

    python -m app.ingestion.run_ingest
    python -m app.ingestion.run_ingest --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from openai import OpenAI

from app.config import get_settings
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.embedder import OpenAIEmbedder
from app.ingestion.orchestrator import run_ingest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest CORPUS_ROOT into RAG chunks")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-ingest files whose source_path already exists (delete + insert)",
    )
    parser.add_argument(
        "--root",
        type=str,
        default="",
        help="Override CORPUS_ROOT for this run",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    root_value = (args.root or settings.corpus_root or "").strip()
    if not root_value:
        print(
            "CORPUS_ROOT is not set. Add it to backend/.env or pass --root.",
            file=sys.stderr,
        )
        return 1
    if not settings.embeddings_configured:
        print("OPENAI_API_KEY is not set.", file=sys.stderr)
        return 1
    if not settings.database_url:
        print("DATABASE_URL is not set.", file=sys.stderr)
        return 1

    corpus_root = Path(root_value).expanduser()
    allowlist = set(settings.corpus_extensions_list)
    embedder = OpenAIEmbedder(
        client=OpenAI(api_key=settings.openai_api_key),
        model=settings.embedding_model,
    )

    print(f"Corpus root: {corpus_root}")
    print(f"Allowlist: {sorted(allowlist)}")
    print(f"Force: {args.force}")

    summary = run_ingest(
        corpus_root=corpus_root,
        allowlist=allowlist,
        session_factory=get_session_factory(),
        embedder=embedder,
        store=ChunkStore(),
        force=args.force,
    )

    print(
        "Summary: "
        f"seen={summary.seen} ingested={summary.ingested} "
        f"skipped_extension={summary.skipped_extension} "
        f"skipped_existing={summary.skipped_existing} "
        f"failed={summary.failed} chunks={summary.chunks}"
    )
    for err in summary.errors[:20]:
        print(f"  error: {err}", file=sys.stderr)
    if len(summary.errors) > 20:
        print(f"  ... and {len(summary.errors) - 20} more errors", file=sys.stderr)

    return 0 if summary.failed == 0 or summary.ingested > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
