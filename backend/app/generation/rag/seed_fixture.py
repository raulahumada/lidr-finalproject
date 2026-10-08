"""CLI: seed one fixture document + embedded chunks for local search demos.

Usage (from backend/ with venv active and DATABASE_URL + OPENAI_API_KEY set):

    python -m app.generation.rag.seed_fixture
"""

from __future__ import annotations

import sys

from openai import OpenAI

from app.config import get_settings
from app.foundation.persistence.database import get_session_factory
from app.foundation.persistence.repository import ChunkStore
from app.generation.rag.embedder import OpenAIEmbedder

FIXTURE_SOURCE = "fixtures/metropol_omnicanal_sample.txt"
FIXTURE_TYPE = "fixture"

# Commit-safe sample paragraphs (Metropol-flavoured, not client confidential docs).
FIXTURE_CHUNKS: list[tuple[str, str]] = [
    (
        "paragraph",
        (
            "Metropol Fintech opera préstamos personales con captación omnicanal. "
            "Los agentes de ventas usan WhatsApp y campañas para contactar leads, "
            "validar identidad vía Tenela y simular ofertas antes del dictamen."
        ),
    ),
    (
        "paragraph",
        (
            "En cobranzas, los avisos de pago y promesas se gestionan con handoff "
            "a humanos cuando el cliente pide hablar con una persona o cuando no "
            "hay evidencia suficiente en la documentación de políticas."
        ),
    ),
    (
        "paragraph",
        (
            "El corpus RAG de la entrega indexa documentación de omnicanalidad, "
            "ventas, cobranzas e integraciones Tenela para que los agentes "
            "respondan con contexto recuperado y citas, no con inventos."
        ),
    ),
]


def main() -> int:
    settings = get_settings()
    if not settings.database_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 1
    if not settings.embeddings_configured:
        print("OPENAI_API_KEY is not set", file=sys.stderr)
        return 1

    embedder = OpenAIEmbedder(
        client=OpenAI(api_key=settings.openai_api_key),
        model=settings.embedding_model,
    )
    store = ChunkStore()
    session_factory = get_session_factory()

    texts = [content for _, content in FIXTURE_CHUNKS]
    vectors = embedder.embed_many(texts)

    with session_factory() as session:
        existing = store.find_document_id(session, FIXTURE_SOURCE)
        if existing is not None:
            print(f"Fixture already present (document_id={existing}); skipping insert.")
            return 0

        chunks = [
            (chunk_type, content, vector, {"fixture": True, "index": index})
            for index, ((chunk_type, content), vector) in enumerate(
                zip(FIXTURE_CHUNKS, vectors)
            )
        ]
        document = store.persist_document_with_chunks(
            session,
            source_path=FIXTURE_SOURCE,
            document_type=FIXTURE_TYPE,
            doc_metadata={"label": "metropol_sample"},
            chunks=chunks,
        )
        session.commit()
        print(
            f"Seeded document_id={document.id} with {len(chunks)} chunks "
            f"(source_path={FIXTURE_SOURCE})."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
