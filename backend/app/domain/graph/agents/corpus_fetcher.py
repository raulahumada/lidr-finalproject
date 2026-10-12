"""Retrieve evidence — the only node allowed to call SemanticRetriever."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from app.domain.graph.state import AgenticAnswerState


def corpus_fetcher(state: AgenticAnswerState, config: RunnableConfig) -> dict[str, Any]:
    retriever = config["configurable"]["retriever"]
    query = state.get("framed_query") or state.get("question") or ""
    k = int(state.get("k") or config["configurable"].get("default_k") or 5)
    search = retriever.search(query=query, k=k)
    hits = [hit.model_dump() for hit in search.results]
    no_evidence = len(hits) == 0
    confidence = 0.0 if no_evidence else min(0.9, 0.45 + (hits[0].get("score") or 0.0) * 0.45)
    return {
        "hits": hits,
        "no_evidence": no_evidence,
        "confidence": confidence,
        "agent_trace": [
            {
                "node": "corpus_fetcher",
                "summary": f"retrieved {len(hits)} hit(s)",
            }
        ],
    }
