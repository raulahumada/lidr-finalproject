"""Answer conductor: response CAG → RAG retrieve → knowledge pack → LLM."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.foundation.llm.chat import ChatClient
from app.foundation.prompts.loader import render_answer_prompts
from app.generation.cag.exact import ExactAnswerCache
from app.generation.cag.semantic import SemanticAnswerCache
from app.generation.rag.knowledge_pack import get_default_knowledge_pack
from app.generation.rag.retriever import SemanticRetriever
from app.schemas.answer import AnswerResponse, Citation
from app.schemas.search import SearchHit

log = logging.getLogger(__name__)

_NO_EVIDENCE = (
    "No encontré evidencia suficiente en el corpus Metropol para responder "
    "con confianza. Recomendación: reformular la pregunta o escalar a un humano."
)


class AnswerService:
    def __init__(
        self,
        *,
        retriever: SemanticRetriever,
        chat: ChatClient,
        exact_cache: ExactAnswerCache | None,
        semantic_cache: SemanticAnswerCache | None,
        knowledge_pack: str,
        prompt_version: str,
        default_k: int,
    ) -> None:
        self.retriever = retriever
        self.chat = chat
        self.exact_cache = exact_cache
        self.semantic_cache = semantic_cache
        self.knowledge_pack = knowledge_pack
        self.prompt_version = prompt_version
        self.default_k = default_k

    def answer(self, *, question: str, k: int | None = None) -> AnswerResponse:
        started = time.perf_counter()
        resolved_k = k if k is not None else self.default_k
        model = self.chat.model

        cache_key = ExactAnswerCache.make_key(
            question=question,
            prompt_version=self.prompt_version,
            model=model,
            k=resolved_k,
        )
        if self.exact_cache is not None:
            hit = self.exact_cache.get(cache_key)
            if hit is not None:
                return self._from_cache_payload(
                    hit, question=question, cached="exact", started=started
                )

        if self.semantic_cache is not None:
            semantic_hit = self.semantic_cache.lookup(
                question=question,
                prompt_version=self.prompt_version,
                model=model,
                k=resolved_k,
            )
            if semantic_hit is not None:
                return self._from_cache_payload(
                    semantic_hit, question=question, cached="semantic", started=started
                )

        search = self.retriever.search(query=question, k=resolved_k)
        if not search.results:
            return AnswerResponse(
                question=question,
                answer=_NO_EVIDENCE,
                citations=[],
                cached="false",
                prompt_version=self.prompt_version,
                k=resolved_k,
                latency_ms=self._elapsed_ms(started),
                no_evidence=True,
            )

        chunk_dicts = [
            {
                "source_path": hit.source_path,
                "content": hit.content,
                "chunk_id": hit.chunk_id,
            }
            for hit in search.results
        ]
        system, user = render_answer_prompts(
            version=self.prompt_version,
            knowledge_pack=self.knowledge_pack,
            question=question,
            retrieved_chunks=chunk_dicts,
        )
        raw = self.chat.complete_json(system=system, user=user)
        answer_text = str(raw.get("answer") or "").strip() or _NO_EVIDENCE
        indices = raw.get("citation_indices") or []
        citations = self._citations_from_indices(search.results, indices)

        response = AnswerResponse(
            question=question,
            answer=answer_text,
            citations=citations,
            cached="false",
            prompt_version=self.prompt_version,
            k=resolved_k,
            latency_ms=self._elapsed_ms(started),
            no_evidence=False,
        )
        payload = response.model_dump()
        if self.exact_cache is not None:
            self.exact_cache.set(cache_key, payload)
        if self.semantic_cache is not None:
            self.semantic_cache.store(
                question=question,
                prompt_version=self.prompt_version,
                model=model,
                k=resolved_k,
                payload=payload,
            )
        return response

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    @staticmethod
    def _citations_from_indices(
        hits: list[SearchHit], indices: Any
    ) -> list[Citation]:
        citations: list[Citation] = []
        if not isinstance(indices, list):
            return citations
        seen: set[int] = set()
        for raw_idx in indices:
            try:
                idx = int(raw_idx)
            except (TypeError, ValueError):
                continue
            if idx < 0 or idx >= len(hits) or idx in seen:
                continue
            seen.add(idx)
            hit = hits[idx]
            citations.append(
                Citation(
                    chunk_id=hit.chunk_id,
                    document_id=hit.document_id,
                    source_path=hit.source_path,
                    document_type=hit.document_type,
                    score=hit.score,
                    excerpt=hit.content[:400],
                    metadata=hit.metadata,
                )
            )
        return citations

    def _from_cache_payload(
        self,
        payload: dict[str, Any],
        *,
        question: str,
        cached: str,
        started: float,
    ) -> AnswerResponse:
        data = dict(payload)
        data["question"] = question
        data["cached"] = cached
        data["latency_ms"] = self._elapsed_ms(started)
        data.setdefault("prompt_version", self.prompt_version)
        return AnswerResponse.model_validate(data)


def build_knowledge_pack(max_tokens: int) -> str:
    return get_default_knowledge_pack(max_tokens)
