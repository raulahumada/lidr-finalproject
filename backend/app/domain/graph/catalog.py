"""Single source of truth for agent catalog (served to the console)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.domain.graph.domain_tag import DOMAINS
from app.domain.graph.orchestrator import FALLBACK_LADDER, effective_ladder
from app.foundation.persistence.database import get_session_factory

log = logging.getLogger(__name__)

_PROMPTS_ROOT = Path(__file__).resolve().parents[2] / "foundation" / "prompts"

_AGENT_META: dict[str, dict[str, Any]] = {
    "orchestrator": {
        "key": "orchestrator",
        "label": "Orquestador",
        "role": "Elige el siguiente especialista (escalera determinista + tope de pasos).",
        "llm_driven": False,
        "tools": [],
        "implementation": (
            "Nodo hub en Python (escalera legal + AGENTIC_ORCHESTRATOR_MAX_STEPS). "
            "No llama al LLM: no tiene system prompt."
        ),
    },
    "intent_framer": {
        "key": "intent_framer",
        "label": "Encuadre de intención",
        "role": "Prepara / resuelve la pregunta para retrieval (incluye memoria de sesión).",
        "llm_driven": False,
        "tools": [],
        "implementation": (
            "Código Python + resolver de memoria de sesión. "
            "No llama al LLM: no tiene system prompt."
        ),
    },
    "corpus_fetcher": {
        "key": "corpus_fetcher",
        "label": "Recuperación de evidencia",
        "role": "Único nodo con acceso al retriever semántico del corpus Metropol.",
        "llm_driven": False,
        "tools": ["search_corpus"],
        "implementation": (
            "Llama al retriever semántico (embeddings). "
            "No llama al LLM: no tiene system prompt."
        ),
    },
    "grounded_composer": {
        "key": "grounded_composer",
        "label": "Síntesis grounded",
        "role": "Redacta la respuesta con citas sobre evidencia recuperada.",
        "llm_driven": True,
        "tools": [],
        "prompt_source": "answer/{version}/system.j2",
        "implementation": (
            "Único builtin que llama al Chat LLM. "
            "System prompt = plantilla Jinja versionada (ANSWER_PROMPT_VERSION)."
        ),
    },
    "source_guard": {
        "key": "source_guard",
        "label": "Validación de citas",
        "role": "Descarta citas que no corresponden a hits recuperados.",
        "llm_driven": False,
        "tools": [],
        "implementation": (
            "Validación determinista de citas vs hits. "
            "No llama al LLM: no tiene system prompt."
        ),
    },
    "escalation_gate": {
        "key": "escalation_gate",
        "label": "Gate de revisión humana",
        "role": "Pausa la corrida cuando hay razones de revisión.",
        "llm_driven": False,
        "tools": [],
        "implementation": (
            "Reglas de confianza / evidencia / citas → interrupt humano. "
            "No llama al LLM: no tiene system prompt."
        ),
    },
}

BUILTIN_KEYS: frozenset[str] = frozenset(_AGENT_META.keys())


def builtin_keys() -> set[str]:
    return set(BUILTIN_KEYS)


def _jinja_preview(relative: str, *, version: str) -> str | None:
    """Read allowlisted Jinja source under foundation/prompts."""
    rel = relative.replace("{version}", version)
    path = (_PROMPTS_ROOT / rel).resolve()
    try:
        path.relative_to(_PROMPTS_ROOT.resolve())
    except ValueError:
        log.warning("prompt_preview_path_escape rel=%s", rel)
        return None
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        log.warning("prompt_preview_read_failed path=%s err=%s", path, exc)
        return None


def _builtin_entry(key: str, *, version: str) -> dict[str, Any]:
    meta = dict(_AGENT_META[key])
    meta["kind"] = "builtin"
    meta["enabled"] = True
    meta["mutable"] = False
    source = meta.pop("prompt_source", None)
    if source and meta.get("llm_driven"):
        meta["prompt_kind"] = "jinja"
        meta["prompt_source"] = source.replace("{version}", version)
        preview = _jinja_preview(source, version=version)
        if preview is not None:
            meta["prompt_preview"] = preview
        meta["prompt_note"] = (
            "System prompt Jinja (solo lectura). Los demás builtins son código, no LLM."
        )
    else:
        meta["prompt_kind"] = "none"
        meta["prompt_preview"] = None
        meta["prompt_note"] = (
            "Este nodo no usa system prompt: es lógica en Python, no una llamada al LLM."
        )
    return meta


def _list_customs_safe() -> list[dict[str, Any]]:
    try:
        from app.domain.graph.agent_store import AgentStore

        store = AgentStore(get_session_factory())
        return store.list_customs()
    except Exception as exc:  # noqa: BLE001 — degrade catalog if DB down
        log.warning("agent_catalog_customs_unavailable: %s", exc)
        return []


def agent_catalog() -> dict[str, Any]:
    """Return builtins + customs + effective ladder + knobs."""
    settings = get_settings()
    version = settings.answer_prompt_version
    order = ("orchestrator", *FALLBACK_LADDER, "escalation_gate")
    builtins = [
        _builtin_entry(key, version=version) for key in order if key in _AGENT_META
    ]
    customs_out = [_enrich_custom(item) for item in _list_customs_safe()]

    return {
        "agents": [*builtins, *customs_out],
        "ladder": effective_ladder(),
        "domains": list(DOMAINS),
        "knobs": {
            "agentic_orchestrator_max_steps": settings.agentic_orchestrator_max_steps,
            "agentic_confidence_threshold": settings.agentic_confidence_threshold,
        },
    }


def _enrich_custom(item: dict[str, Any]) -> dict[str, Any]:
    row = dict(item)
    row["mutable"] = True
    row["prompt_kind"] = "db"
    row["prompt_preview"] = row.get("system_prompt")
    row["prompt_note"] = "System prompt persistido en Postgres (editable)."
    row["implementation"] = (
        "Nodo genérico prompt_specialist: LLM con el system prompt del perfil."
    )
    return row


def get_agent_detail(key: str) -> dict[str, Any] | None:
    settings = get_settings()
    if key in _AGENT_META:
        return _builtin_entry(key, version=settings.answer_prompt_version)
    for item in _list_customs_safe():
        if item["key"] == key:
            return _enrich_custom(item)
    return None
