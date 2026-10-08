"""Data access for documents/chunks (caller owns the Session/transaction)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Row, select
from sqlalchemy.orm import Session

from app.foundation.persistence.models import ChunkRow, DocumentRow


@dataclass(frozen=True)
class RankedChunk:
    id: int
    document_id: int
    chunk_type: str
    content: str
    distance: float
    metadata: dict
    source_path: str
    document_type: str


class ChunkStore:
    def find_document_id(self, session: Session, source_path: str) -> int | None:
        stmt = select(DocumentRow.id).where(DocumentRow.source_path == source_path)
        return session.execute(stmt).scalar_one_or_none()

    def persist_document_with_chunks(
        self,
        session: Session,
        *,
        source_path: str,
        document_type: str,
        doc_metadata: dict,
        chunks: list[tuple[str, str, list[float] | None, dict]],
    ) -> DocumentRow:
        """Insert document + chunks.

        Each chunk tuple is ``(chunk_type, content, embedding | None, metadata)``.
        """
        document = DocumentRow(
            source_path=source_path,
            document_type=document_type,
            metadata_=doc_metadata,
        )
        session.add(document)
        session.flush()

        for chunk_type, content, embedding, metadata in chunks:
            session.add(
                ChunkRow(
                    document_id=document.id,
                    chunk_type=chunk_type,
                    content=content,
                    embedding=embedding,
                    metadata_=metadata,
                )
            )
        session.flush()
        return document

    def search_by_embedding(
        self,
        session: Session,
        *,
        query_vector: list[float],
        k: int,
    ) -> list[RankedChunk]:
        distance = ChunkRow.embedding.cosine_distance(query_vector)
        stmt = (
            select(ChunkRow, DocumentRow, distance.label("distance"))
            .join(DocumentRow, DocumentRow.id == ChunkRow.document_id)
            .where(ChunkRow.embedding.is_not(None))
            .order_by(distance)
            .limit(k)
        )
        rows: list[Row] = list(session.execute(stmt).all())
        return [
            RankedChunk(
                id=chunk.id,
                document_id=chunk.document_id,
                chunk_type=chunk.chunk_type,
                content=chunk.content,
                distance=float(dist),
                metadata=dict(chunk.metadata_ or {}),
                source_path=document.source_path,
                document_type=document.document_type,
            )
            for chunk, document, dist in rows
        ]
