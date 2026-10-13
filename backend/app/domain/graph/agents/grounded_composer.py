"""Compose a grounded answer using prompts v2 + ChatClient (no CAG)."""

from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig

from app.domain.answer_service import AnswerService
from app.domain.graph.state import AgenticAnswerState
from app.foundation.prompts.loader import render_answer_prompts
from app.generation.conversation.budget import render_memory
from app.generation.rag.context_blocks import build_context, fit_to_budget
from app.schemas.search import SearchHit

_NO_EVIDENCE = (
    "No encontré evidencia suficiente en el corpus Metropol para responder "
    "con confianza. Recomendación: reformular la pregunta o escalar a un humano."
)


def grounded_composer(state: AgenticAnswerState, config: RunnableConfig) -> dict[str, Any]:
    cfg = config["configurable"]
    hits_raw = state.get("hits") or []
    if not hits_raw or state.get("no_evidence"):
        return {
            "answer": _NO_EVIDENCE,
            "citations": [],
            "no_evidence": True,
            "confidence": 0.0,
            "agent_trace": [
                {
                    "node": "grounded_composer",
                    "summary": "no evidence — skipped LLM",
                }
            ],
        }

    hits = [SearchHit.model_validate(h) for h in hits_raw]
    max_tokens = int(cfg.get("context_max_tokens") or 3500)
    memory_budget = int(cfg.get("conversation_memory_max_tokens") or 1024)
    memory = render_memory(
        list(state.get("conversation_window") or []),
        budget=memory_budget,
    )
    memory_text = memory.text if memory else ""
    memory_tokens = memory.tokens_used if memory else 0
    # Evidence wins: charge memory inside the context budget, never on top.
    evidence_budget = max(500, max_tokens - memory_tokens)

    blocks = fit_to_budget(hits, max_tokens=evidence_budget)
    if not blocks:
        return {
            "answer": _NO_EVIDENCE,
            "citations": [],
            "no_evidence": True,
            "confidence": 0.0,
            "agent_trace": [
                {
                    "node": "grounded_composer",
                    "summary": "budget dropped all blocks — skipped LLM",
                }
            ],
        }

    prompt_version = str(cfg.get("prompt_version") or "v2")
    knowledge_pack = str(cfg.get("knowledge_pack") or "")
    question = (
        state.get("resolved_question") or state.get("question") or ""
    )
    if prompt_version == "v1":
        system, user = render_answer_prompts(
            version="v1",
            knowledge_pack=knowledge_pack,
            question=question,
            retrieved_chunks=[
                {
                    "source_path": b.hit.source_path,
                    "content": b.hit.content,
                    "chunk_id": b.hit.chunk_id,
                }
                for b in blocks
            ],
            memory_block=memory_text,
        )
    else:
        system, user = render_answer_prompts(
            version=prompt_version,
            knowledge_pack=knowledge_pack,
            question=question,
            context=build_context(blocks),
            memory_block=memory_text,
        )

    chat = cfg["chat"]
    raw = chat.complete_json(system=system, user=user)
    answer_text = str(raw.get("answer") or "").strip() or _NO_EVIDENCE
    citations = [
        c.model_dump() for c in AnswerService._citations_from_model(blocks, raw)
    ]
    summary = f"composed answer with {len(citations)} citation(s)"
    if memory:
        summary += f"; memory {memory.turns_included} turn(s)"
        if memory.trimmed:
            summary += f" (dropped {memory.turns_dropped})"
    return {
        "answer": answer_text,
        "citations": citations,
        "no_evidence": False,
        "prompt_version": prompt_version,
        "agent_trace": [
            {
                "node": "grounded_composer",
                "summary": summary,
            }
        ],
    }
