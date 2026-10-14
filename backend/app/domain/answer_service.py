"""Answer conductor: response CAG → RAG retrieve → knowledge pack → LLM."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.domain.grounding import NO_EVIDENCE_ANSWER
from app.foundation.llm.chat import ChatClient
from app.foundation.llm.usage import Usage
from app.foundation.prompts.loader import render_answer_prompts
from app.generation.cag.exact import ExactAnswerCache
from app.generation.cag.semantic import SemanticAnswerCache
from app.generation.rag.context_blocks import ContextBlock, build_context, fit_to_budget
from app.generation.rag.knowledge_pack import get_default_knowledge_pack
from app.generation.rag.retriever import SemanticRetriever
from app.schemas.answer import AnswerResponse, Citation
from app.schemas.search import SearchHit
from app.schemas.usage import TokenUsage

log = logging.getLogger(__name__)


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
        context_max_tokens: int = 3500,
    ) -> None:
        self.retriever = retriever
        self.chat = chat
        self.exact_cache = exact_cache
        self.semantic_cache = semantic_cache
        self.knowledge_pack = knowledge_pack
        self.prompt_version = prompt_version
        self.default_k = default_k
        self.context_max_tokens = context_max_tokens

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
                answer=NO_EVIDENCE_ANSWER,
                citations=[],
                cached="false",
                prompt_version=self.prompt_version,
                k=resolved_k,
                latency_ms=self._elapsed_ms(started),
                no_evidence=True,
                usage=self._token_usage(Usage.unreported()),
            )

        blocks = fit_to_budget(
            search.results, max_tokens=self.context_max_tokens
        )
        if not blocks:
            return AnswerResponse(
                question=question,
                answer=NO_EVIDENCE_ANSWER,
                citations=[],
                cached="false",
                prompt_version=self.prompt_version,
                k=resolved_k,
                latency_ms=self._elapsed_ms(started),
                no_evidence=True,
                usage=self._token_usage(Usage.unreported()),
            )

        system, user = self._render_prompts(question=question, blocks=blocks)
        raw = self.chat.complete_json(system=system, user=user, role="chat")
        answer_text = str(raw.get("answer") or "").strip() or NO_EVIDENCE_ANSWER
        citations = self._citations_from_model(blocks, raw)

        response = AnswerResponse(
            question=question,
            answer=answer_text,
            citations=citations,
            cached="false",
            prompt_version=self.prompt_version,
            k=resolved_k,
            latency_ms=self._elapsed_ms(started),
            no_evidence=False,
            usage=self._token_usage(
                getattr(self.chat, "last_usage", None) or Usage.unreported()
            ),
        )
        payload = response.model_dump()
        # Cached bodies must not replay billed usage on a later hit.
        payload["usage"] = TokenUsage().model_dump()
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

    def _render_prompts(
        self, *, question: str, blocks: list[ContextBlock]
    ) -> tuple[str, str]:
        if self.prompt_version == "v1":
            chunk_dicts = [
                {
                    "source_path": block.hit.source_path,
                    "content": block.hit.content,
                    "chunk_id": block.hit.chunk_id,
                }
                for block in blocks
            ]
            return render_answer_prompts(
                version="v1",
                knowledge_pack=self.knowledge_pack,
                question=question,
                retrieved_chunks=chunk_dicts,
            )
        return render_answer_prompts(
            version=self.prompt_version,
            knowledge_pack=self.knowledge_pack,
            question=question,
            context=build_context(blocks),
        )

    @staticmethod
    def _elapsed_ms(started: float) -> int:
        return int((time.perf_counter() - started) * 1000)

    @staticmethod
    def _hit_to_citation(hit: SearchHit) -> Citation:
        return Citation(
            chunk_id=hit.chunk_id,
            document_id=hit.document_id,
            source_path=hit.source_path,
            document_type=hit.document_type,
            score=hit.score,
            excerpt=hit.content[:400],
            metadata=hit.metadata,
        )

    @classmethod
    def _citations_from_model(
        cls, blocks: list[ContextBlock], raw: dict[str, Any]
    ) -> list[Citation]:
        by_chunk_id = {block.hit.chunk_id: block.hit for block in blocks}
        citations: list[Citation] = []
        seen: set[int] = set()

        def add_hit(hit: SearchHit) -> None:
            if hit.chunk_id in seen:
                return
            seen.add(hit.chunk_id)
            citations.append(cls._hit_to_citation(hit))

        ids = raw.get("citation_ids")
        if isinstance(ids, list):
            for raw_id in ids:
                try:
                    chunk_id = int(raw_id)
                except (TypeError, ValueError):
                    continue
                hit = by_chunk_id.get(chunk_id)
                if hit is not None:
                    add_hit(hit)

        indices = raw.get("citation_indices")
        if isinstance(indices, list):
            for raw_idx in indices:
                try:
                    idx = int(raw_idx)
                except (TypeError, ValueError):
                    continue
                # Prefer block index; also accept mistaken chunk_id in indices.
                if 0 <= idx < len(blocks):
                    add_hit(blocks[idx].hit)
                elif idx in by_chunk_id:
                    add_hit(by_chunk_id[idx])

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
        # Cache hits never bill — always unreported zeros.
        data["usage"] = TokenUsage().model_dump()
        return AnswerResponse.model_validate(data)

    @staticmethod
    def _token_usage(usage: Usage) -> TokenUsage:
        return TokenUsage(
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            reported=usage.reported,
        )


def build_knowledge_pack(max_tokens: int) -> str:
    return get_default_knowledge_pack(max_tokens)
