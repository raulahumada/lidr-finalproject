"""Thin HTTP layer for semantic search."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_semantic_retriever
from app.generation.rag.retriever import SemanticRetriever
from app.schemas.search import SearchRequest, SearchResponse

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
def search(
    request: SearchRequest,
    retriever: Optional[SemanticRetriever] = Depends(get_semantic_retriever),
) -> SearchResponse:
    if retriever is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service is not available.",
        )
    try:
        return retriever.search(query=request.query, k=request.k)
    except Exception as exc:  # noqa: BLE001 — surface as 500; detail logged by server
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run semantic search.",
        ) from exc
