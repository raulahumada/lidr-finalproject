"""In-process activity log for live agentic progress polling.

Bridges blocking graph runs and the frontend the same way the course
``agents_event`` / peer pattern does: consume ``graph.stream(..., stream_mode=
"updates")`` node by node, narrate with ``describe_node``, buffer per
``thread_id`` for ``GET .../progress``.

Single-process dict only — fine for local one-worker Uvicorn. Multi-worker
needs a shared store later.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

RunStatus = Literal["running", "completed", "awaiting_human_review", "failed"]

_LABELS: dict[str, str] = {
    "orchestrator": "Orquestador",
    "intent_framer": "Encuadre de intención",
    "corpus_fetcher": "Recuperación de evidencia",
    "prompt_specialist": "Agente custom",
    "grounded_composer": "Síntesis grounded",
    "source_guard": "Validación de citas",
    "escalation_gate": "Gate de revisión",
}


@dataclass
class ActivityEntry:
    node: str
    label: str
    message: str
    at: float = field(default_factory=time.time)


@dataclass
class ActivityRun:
    status: RunStatus = "running"
    entries: list[ActivityEntry] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    question: str | None = None
    custom_notes: list[dict[str, str]] = field(default_factory=list)
    last_usage: dict[str, Any] | None = None


class GraphActivityLog:
    """Per-thread_id activity buffer for live progress polling."""

    def __init__(self) -> None:
        self._runs: dict[str, ActivityRun] = {}

    def start(self, thread_id: str, *, question: str | None = None) -> None:
        self._runs[thread_id] = ActivityRun(question=question)

    def append(self, thread_id: str, node: str, label: str, message: str) -> None:
        run = self._runs.setdefault(thread_id, ActivityRun())
        run.entries.append(ActivityEntry(node=node, label=label, message=message))

    def extend_custom_notes(
        self, thread_id: str, notes: list[dict[str, Any]] | None
    ) -> None:
        """Accumulate custom agent notes for live progress while still running."""
        if not notes:
            return
        run = self._runs.setdefault(thread_id, ActivityRun())
        for item in notes:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip()
            note = str(item.get("note") or "").strip()
            if key and note:
                run.custom_notes.append({"key": key, "note": note})

    def set_usage(self, thread_id: str, usage: dict[str, Any]) -> None:
        """Store last completion usage for live progress while still running."""
        run = self._runs.setdefault(thread_id, ActivityRun())
        run.last_usage = dict(usage)

    def finish(
        self,
        thread_id: str,
        status: RunStatus,
        *,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        run = self._runs.setdefault(thread_id, ActivityRun())
        run.status = status
        run.result = result
        run.error = error

    def read(self, thread_id: str) -> ActivityRun | None:
        return self._runs.get(thread_id)


def describe_node(node_name: str, update: Any) -> list[dict[str, str]]:
    """Translate one node's raw update into human-readable activity lines.

    Pure and exception-free: narration must never take down the run.
    """
    try:
        return _describe(node_name, update)
    except Exception:  # noqa: BLE001
        label = _LABELS.get(node_name, node_name)
        return [{"node": node_name, "label": label, "message": "…"}]


def _describe(node_name: str, update: Any) -> list[dict[str, str]]:
    if node_name == "__interrupt__":
        return _describe_interrupt(update)

    update = update or {}
    label = _LABELS.get(node_name, node_name)

    # Prefer agent_trace summary when nodes already emit one.
    trace = update.get("agent_trace") or []
    if isinstance(trace, list) and trace:
        last = trace[-1] if isinstance(trace[-1], dict) else {}
        summary = str(last.get("summary") or "").strip()
        if summary:
            return [{"node": node_name, "label": label, "message": summary}]

    if node_name == "orchestrator":
        next_agent = update.get("next_agent") or ""
        reason = str(update.get("route_reason") or "").strip()
        if next_agent and reason:
            message = f"elige {next_agent}: {reason}"
        elif next_agent:
            message = f"elige {next_agent}"
        else:
            message = "decisión de ruteo"
        return [{"node": node_name, "label": label, "message": message}]

    if node_name == "intent_framer":
        framed = update.get("framed_query") or ""
        message = "consulta encuadrada para retrieval" if framed else "encuadre listo"
        return [{"node": node_name, "label": label, "message": message}]

    if node_name == "corpus_fetcher":
        hits = update.get("hits") or []
        if update.get("no_evidence") or not hits:
            message = "sin evidencia en el corpus"
        else:
            message = f"{len(hits)} chunk(s) recuperados"
        return [{"node": node_name, "label": label, "message": message}]

    if node_name == "grounded_composer":
        answer = update.get("answer") or ""
        citations = update.get("citations") or []
        if not answer:
            message = "sin respuesta generada"
        else:
            message = (
                f"respuesta generada ({len(answer)} caracteres) "
                f"sobre {len(citations)} cita(s)"
            )
        return [{"node": node_name, "label": label, "message": message}]

    if node_name == "source_guard":
        valid = update.get("citations_valid")
        if valid is True:
            message = "citas respaldadas por evidencia"
        elif valid is False:
            message = "citas inválidas o sin respaldo"
        else:
            message = "validación de citas completada"
        return [{"node": node_name, "label": label, "message": message}]

    if node_name == "escalation_gate":
        reasons = update.get("review_reasons") or []
        decision = update.get("human_decision")
        if decision is not None:
            action = (
                (decision or {}).get("decision")
                or (decision or {}).get("action")
                or "approve"
            )
            message = f"decisión humana: {action}"
        elif reasons:
            message = "esperando revisión humana: " + "; ".join(str(r) for r in reasons)
        elif update.get("status") == "completed":
            message = "sin disparadores — respuesta lista"
        else:
            message = "gate evaluado"
        return [{"node": node_name, "label": label, "message": message}]

    return [{"node": node_name, "label": label, "message": "actualizó el estado"}]


def _describe_interrupt(update: Any) -> list[dict[str, str]]:
    reasons: list[str] = []
    try:
        for item in update or ():
            value = getattr(item, "value", None) or {}
            if isinstance(value, dict):
                reasons.extend(value.get("reasons") or [])
    except TypeError:
        pass
    message = "esperando revisión humana"
    if reasons:
        message += ": " + "; ".join(str(r) for r in reasons)
    return [
        {
            "node": "escalation_gate",
            "label": _LABELS["escalation_gate"],
            "message": message,
        }
    ]
