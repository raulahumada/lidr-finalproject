"""HTTP tests for POST /api/v1/search."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.dependencies import get_semantic_retriever
from app.main import app
from app.schemas.search import SearchHit, SearchResponse


class _FakeRetriever:
    def __init__(self, hits: list[SearchHit] | None = None) -> None:
        self.hits = hits or []

    def search(self, *, query: str, k: int) -> SearchResponse:
        return SearchResponse(
            query=query,
            k=k,
            search_time_ms=12,
            results=self.hits[:k],
        )


def test_search_empty_corpus_returns_200() -> None:
    app.dependency_overrides[get_semantic_retriever] = lambda: _FakeRetriever([])
    try:
        response = TestClient(app).post("/api/v1/search", json={"query": "cobranzas", "k": 5})
        assert response.status_code == 200
        body = response.json()
        assert body["query"] == "cobranzas"
        assert body["k"] == 5
        assert body["results"] == []
        assert body["search_time_ms"] == 12
    finally:
        app.dependency_overrides.clear()


def test_search_returns_ranked_hits() -> None:
    hit = SearchHit(
        chunk_id=1,
        document_id=9,
        chunk_type="paragraph",
        content="Avisos de pago y promesas en cobranzas.",
        score=0.91,
        distance=0.09,
        source_path="fixtures/metropol_omnicanal_sample.txt",
        document_type="fixture",
        metadata={"fixture": True},
    )
    app.dependency_overrides[get_semantic_retriever] = lambda: _FakeRetriever([hit])
    try:
        response = TestClient(app).post("/api/v1/search", json={"query": "cobranzas", "k": 3})
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["chunk_id"] == 1
        assert results[0]["score"] == 0.91
    finally:
        app.dependency_overrides.clear()


def test_search_k_out_of_bounds_returns_422() -> None:
    app.dependency_overrides[get_semantic_retriever] = lambda: _FakeRetriever([])
    try:
        response = TestClient(app).post("/api/v1/search", json={"query": "x", "k": 0})
        assert response.status_code == 422
        response = TestClient(app).post("/api/v1/search", json={"query": "x", "k": 51})
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_search_without_embeddings_returns_503() -> None:
    app.dependency_overrides[get_semantic_retriever] = lambda: None
    try:
        response = TestClient(app).post("/api/v1/search", json={"query": "ventas"})
        assert response.status_code == 503
        assert "Embedding" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_openapi_lists_search() -> None:
    schema = TestClient(app).get("/openapi.json").json()
    assert "/api/v1/search" in schema["paths"]
    assert "post" in schema["paths"]["/api/v1/search"]
