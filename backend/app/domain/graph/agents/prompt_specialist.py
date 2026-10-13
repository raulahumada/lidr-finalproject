"""Generic LLM step for custom agent profiles stored in Postgres."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.domain.graph.state import AgenticAnswerState

log = logging.getLogger(__name__)


def prompt_specialist(state: AgenticAnswerState, config: RunnableConfig) -> dict[str, Any]:
    """Run the custom profile named in ``next_agent`` (set by the orchestrator)."""
    cfg = config["configurable"]
    key = str(state.get("next_agent") or "").strip()
    if not key:
        return {
            "agent_trace": [
                {"node": "prompt_specialist", "summary": "skipped — no next_agent"}
            ]
        }

    from app.domain.graph.agent_store import AgentStore
    from app.foundation.persistence.database import get_session_factory

    store = AgentStore(get_session_factory())
    system = store.get_system_prompt(key)
    if not system:
        return {
            "agent_trace": [
                {
                    "node": "prompt_specialist",
                    "summary": f"custom {key!r} missing or disabled",
                }
            ]
        }

    chat = cfg.get("chat")
    if chat is None:
        return {
            "agent_trace": [
                {
                    "node": "prompt_specialist",
                    "summary": f"custom {key!r} skipped — no chat client",
                }
            ]
        }

    question = (
        state.get("framed_query")
        or state.get("resolved_question")
        or state.get("question")
        or ""
    )
    hits = state.get("hits") or []
    evidence_bits = []
    for hit in hits[:3]:
        if isinstance(hit, dict):
            excerpt = str(hit.get("excerpt") or hit.get("content") or "")[:240]
            if excerpt:
                evidence_bits.append(excerpt)
    evidence = "\n---\n".join(evidence_bits) if evidence_bits else "(sin excerpts)"

    user = (
        f"Pregunta:\n{question}\n\n"
        f"Evidencia recuperada (extractos):\n{evidence}\n\n"
        'Respondé en JSON: {"note": "tu aporte breve para el compositor"}'
    )
    try:
        raw = chat.complete_json(system=system, user=user)
        note = str(raw.get("note") or "").strip() or str(raw)
    except Exception as exc:  # noqa: BLE001
        log.warning("prompt_specialist_failed key=%s err=%s", key, exc)
        note = f"(error ejecutando {key}: {exc})"

    return {
        "custom_notes": [{"key": key, "note": note}],
        "agent_trace": [
            {
                "node": "prompt_specialist",
                "summary": f"custom {key}: {note[:120]}",
            }
        ],
    }
