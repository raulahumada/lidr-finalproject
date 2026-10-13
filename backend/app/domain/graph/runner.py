"""Invoke and resume the agentic answer graph."""

from __future__ import annotations

import logging
import threading
import uuid
from typing import Any

from langgraph.types import Command

from app.config import Settings, get_settings
from app.domain.answer_service import build_knowledge_pack
from app.domain.graph.activity import GraphActivityLog, describe_node
from app.domain.graph.build import build_agentic_answer_graph
from app.domain.graph.checkpointer import get_checkpointer
from app.domain.graph.state import AgenticAnswerState
from app.foundation.llm.chat import ChatClient
from app.generation.conversation.store import SessionNotFoundError, SessionStore
from app.generation.rag.retriever import SemanticRetriever
from app.schemas.agentic_answer import (
    AgenticAnswerResponse,
    AgentTraceStep,
)
from app.schemas.answer import Citation

log = logging.getLogger(__name__)

THREAD_PREFIX = "agentic-answer"

# Strong refs so background runs are not GC'd mid-flight (peer Task set pattern).
_BACKGROUND_THREADS: set[threading.Thread] = set()


class AgenticAnswerRunner:
    def __init__(
        self,
        *,
        retriever: SemanticRetriever,
        chat: ChatClient,
        settings: Settings | None = None,
        activity_log: GraphActivityLog | None = None,
        session_store: SessionStore | None = None,
    ) -> None:
        self.retriever = retriever
        self.chat = chat
        self.settings = settings or get_settings()
        self.activity_log = activity_log or GraphActivityLog()
        self.session_store = session_store
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
                "conversation_memory_max_tokens": settings.conversation_memory_max_tokens,
            }
        }

    def _conversation_window(self, session_id: str | None) -> list[dict[str, Any]]:
        if not session_id or self.session_store is None:
            return []
        view = self.session_store.get(session_id)
        if view is None:
            return []
        history = list(view.get("history") or [])
        max_turns = max(1, int(self.settings.conversation_max_turns))
        return history[-max_turns:]

    def _initial_state(
        self,
        *,
        question: str,
        resolved_k: int,
        session_id: str | None,
    ) -> AgenticAnswerState:
        initial: AgenticAnswerState = {
            "question": question,
            "k": resolved_k,
            "agent_trace": [],
            "review_reasons": [],
            "prompt_version": self.settings.answer_prompt_version,
            "conversation_window": self._conversation_window(session_id),
        }
        if session_id:
            initial["session_id"] = session_id
        return initial

    def _maybe_append_history(
        self,
        response: AgenticAnswerResponse,
        *,
        session_id: str | None,
    ) -> None:
        if not session_id or self.session_store is None:
            return
        if response.status not in {"completed", "rejected"}:
            return
        try:
            self.session_store.append_turn(
                session_id,
                question=response.question,
                answer=response.answer,
                citations=[c.model_dump() for c in response.citations],
                status=response.status,
                thread_id=response.thread_id,
                resolved_question=response.resolved_question,
            )
        except SessionNotFoundError:
            log.warning(
                "session_append_skipped_missing session_id=%s thread_id=%s",
                session_id,
                response.thread_id,
            )
        except Exception:  # noqa: BLE001
            log.exception(
                "session_append_failed session_id=%s thread_id=%s",
                session_id,
                response.thread_id,
            )

    def start(
        self,
        *,
        question: str,
        k: int | None = None,
        session_id: str | None = None,
    ) -> AgenticAnswerResponse:
        thread_id = uuid.uuid4().hex
        settings = self.settings
        resolved_k = k if k is not None else settings.answer_default_k
        initial = self._initial_state(
            question=question,
            resolved_k=resolved_k,
            session_id=session_id,
        )
        result = self._graph.invoke(initial, self._config(thread_id))
        response = self._to_response(thread_id, result, resolved_k=resolved_k)
        self._maybe_append_history(
            response,
            session_id=session_id or result.get("session_id"),
        )
        return response

    def start_background_run(
        self,
        *,
        question: str,
        k: int | None = None,
        session_id: str | None = None,
    ) -> str:
        """Schedule a streamed graph run; return thread_id immediately."""
        thread_id = uuid.uuid4().hex
        resolved_k = k if k is not None else self.settings.answer_default_k
        self.activity_log.start(thread_id, question=question)

        def _run() -> None:
            try:
                self._run_background(
                    thread_id=thread_id,
                    question=question,
                    resolved_k=resolved_k,
                    session_id=session_id,
                )
            finally:
                _BACKGROUND_THREADS.discard(worker)

        worker = threading.Thread(
            target=_run,
            name=f"agentic-bg-{thread_id[:8]}",
            daemon=True,
        )
        _BACKGROUND_THREADS.add(worker)
        worker.start()
        return thread_id

    def _run_background(
        self,
        *,
        thread_id: str,
        question: str,
        resolved_k: int,
        session_id: str | None = None,
    ) -> None:
        cfg = self._config(thread_id)
        initial = self._initial_state(
            question=question,
            resolved_k=resolved_k,
            session_id=session_id,
        )
        try:
            for update in self._graph.stream(initial, cfg, stream_mode="updates"):
                if not isinstance(update, dict):
                    continue
                for node_name, node_update in update.items():
                    for entry in describe_node(node_name, node_update):
                        self.activity_log.append(
                            thread_id,
                            entry["node"],
                            entry["label"],
                            entry["message"],
                        )

            snapshot = self._graph.get_state(cfg)
            values = dict(snapshot.values or {})
            interrupts = list(getattr(snapshot, "interrupts", None) or ())
            if not interrupts and snapshot.tasks:
                for task in snapshot.tasks:
                    interrupts.extend(getattr(task, "interrupts", None) or ())

            if interrupts:
                payload = (
                    interrupts[0].value
                    if hasattr(interrupts[0], "value")
                    else interrupts[0]
                )
                reasons = list(
                    (payload or {}).get("reasons")
                    or values.get("review_reasons")
                    or []
                )
                for entry in describe_node("__interrupt__", interrupts):
                    self.activity_log.append(
                        thread_id,
                        entry["node"],
                        entry["label"],
                        entry["message"],
                    )
                result = self._to_response(
                    thread_id,
                    {**values, "__interrupt__": interrupts},
                    resolved_k=resolved_k,
                )
                self.activity_log.finish(
                    thread_id,
                    "awaiting_human_review",
                    result=result.model_dump(),
                )
                return

            result = self._to_response(thread_id, values, resolved_k=resolved_k)
            status = result.status
            if status not in {"completed", "rejected", "awaiting_human_review"}:
                status = "completed"
            self.activity_log.finish(
                thread_id,
                status,  # type: ignore[arg-type]
                result=result.model_dump(),
            )
            self._maybe_append_history(
                result,
                session_id=session_id or values.get("session_id"),
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("agentic_background_failed thread_id=%s", thread_id)
            self.activity_log.finish(
                thread_id,
                "failed",
                error=str(exc)[:300],
            )

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

        session_id = (snapshot.values or {}).get("session_id")
        payload = {
            "decision": decision,
            "note": note,
            "adjusted_answer": adjusted_answer,
        }
        result = self._graph.invoke(Command(resume=payload), cfg)
        response = self._to_response(
            thread_id,
            result,
            resolved_k=int(result.get("k") or self.settings.answer_default_k),
        )
        self._maybe_append_history(
            response,
            session_id=session_id or result.get("session_id"),
        )
        return response

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
                resolved_question=self._optional_resolved(result),
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
            resolved_question=self._optional_resolved(result),
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
    def _optional_resolved(result: dict[str, Any]) -> str | None:
        written = str(result.get("question") or "").strip()
        resolved = str(result.get("resolved_question") or "").strip()
        if not resolved or resolved == written:
            substituted = result.get("resolved_substituted") or []
            if not substituted:
                return None
        return resolved or None


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
