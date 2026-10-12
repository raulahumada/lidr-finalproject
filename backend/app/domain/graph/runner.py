"""Invoke and resume the agentic answer graph."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from langgraph.types import Command

from app.config import Settings, get_settings
from app.domain.answer_service import build_knowledge_pack
from app.domain.graph.build import build_agentic_answer_graph
from app.domain.graph.checkpointer import get_checkpointer
from app.domain.graph.state import AgenticAnswerState
from app.foundation.llm.chat import ChatClient
from app.generation.rag.retriever import SemanticRetriever
from app.schemas.agentic_answer import (
    AgenticAnswerResponse,
    AgentTraceStep,
)
from app.schemas.answer import Citation

log = logging.getLogger(__name__)

THREAD_PREFIX = "agentic-answer"


class AgenticAnswerRunner:
    def __init__(
        self,
        *,
        retriever: SemanticRetriever,
        chat: ChatClient,
        settings: Settings | None = None,
    ) -> None:
        self.retriever = retriever
        self.chat = chat
        self.settings = settings or get_settings()
        self._graph = build_agentic_answer_graph(checkpointer=get_checkpointer())

    def _config(self, thread_id: str) -> dict[str, Any]:
        settings = self.settings
        return {
            "configurable": {
                "thread_id": f"{THREAD_PREFIX}:{thread_id}",
                "retriever": self.retriever,
                "chat": self.chat,
                "default_k": settings.answer_default_k,
                "context_max_tokens": settings.answer_context_max_tokens,
                "prompt_version": settings.answer_prompt_version,
                "knowledge_pack": build_knowledge_pack(settings.knowledge_pack_max_tokens),
            }
        }

    def start(self, *, question: str, k: int | None = None) -> AgenticAnswerResponse:
        thread_id = uuid.uuid4().hex
        settings = self.settings
        resolved_k = k if k is not None else settings.answer_default_k
        initial: AgenticAnswerState = {
            "question": question,
            "k": resolved_k,
            "agent_trace": [],
            "review_reasons": [],
            "prompt_version": settings.answer_prompt_version,
        }
        result = self._graph.invoke(initial, self._config(thread_id))
        return self._to_response(thread_id, result, resolved_k=resolved_k)

    def resume(
        self,
        *,
        thread_id: str,
        decision: str,
        note: str | None = None,
        adjusted_answer: str | None = None,
    ) -> AgenticAnswerResponse:
        cfg = self._config(thread_id)
        snapshot = self._graph.get_state(cfg)
        if not snapshot.values:
            raise KeyError(thread_id)
        pending = bool(snapshot.interrupts) or any(
            getattr(task, "interrupts", None) for task in (snapshot.tasks or ())
        )
        if not pending:
            raise KeyError(thread_id)

        payload = {
            "decision": decision,
            "note": note,
            "adjusted_answer": adjusted_answer,
        }
        result = self._graph.invoke(Command(resume=payload), cfg)
        return self._to_response(
            thread_id,
            result,
            resolved_k=int(result.get("k") or self.settings.answer_default_k),
        )

    def _to_response(
        self,
        thread_id: str,
        result: dict[str, Any],
        *,
        resolved_k: int,
    ) -> AgenticAnswerResponse:
        interrupts = result.get("__interrupt__") or []
        if interrupts:
            payload = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
            reasons = list((payload or {}).get("reasons") or result.get("review_reasons") or [])
            return AgenticAnswerResponse(
                status="awaiting_human_review",
                thread_id=thread_id,
                question=str(result.get("question") or ""),
                answer=result.get("answer"),
                citations=self._citations(result.get("citations") or []),
                agent_trace=self._trace(result.get("agent_trace") or []),
                review_reasons=reasons,
                confidence=result.get("confidence"),
                no_evidence=bool(result.get("no_evidence")),
                citations_valid=result.get("citations_valid"),
                prompt_version=result.get("prompt_version"),
                k=resolved_k,
                interrupt_payload=payload if isinstance(payload, dict) else None,
            )

        status = str(result.get("status") or "completed")
        if status not in {"completed", "rejected", "awaiting_human_review"}:
            status = "completed"
        return AgenticAnswerResponse(
            status=status,  # type: ignore[arg-type]
            thread_id=thread_id,
            question=str(result.get("question") or ""),
            answer=result.get("answer"),
            citations=self._citations(result.get("citations") or []),
            agent_trace=self._trace(result.get("agent_trace") or []),
            review_reasons=list(result.get("review_reasons") or []),
            confidence=result.get("confidence"),
            no_evidence=bool(result.get("no_evidence")),
            citations_valid=result.get("citations_valid"),
            prompt_version=result.get("prompt_version"),
            k=resolved_k,
        )

    @staticmethod
    def _citations(raw: list[dict[str, Any]]) -> list[Citation]:
        out: list[Citation] = []
        for item in raw:
            try:
                out.append(Citation.model_validate(item))
            except Exception:  # noqa: BLE001
                continue
        return out

    @staticmethod
    def _trace(raw: list[dict[str, Any]]) -> list[AgentTraceStep]:
        steps: list[AgentTraceStep] = []
        for item in raw:
            node = str(item.get("node") or "")
            summary = str(item.get("summary") or "")
            if node:
                steps.append(AgentTraceStep(node=node, summary=summary))
        return steps
