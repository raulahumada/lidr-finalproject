"""Single source of truth for agent catalog (served to the console)."""

from __future__ import annotations

from typing import Any

from app.config import get_settings
from app.domain.graph.domain_tag import DOMAINS
from app.domain.graph.orchestrator import FALLBACK_LADDER

_AGENT_META: dict[str, dict[str, Any]] = {
    "orchestrator": {
        "key": "orchestrator",
        "label": "Orquestador",
        "role": "Elige el siguiente especialista (escalera determinista + tope de pasos).",
        "llm_driven": False,
        "tools": [],
    },
    "intent_framer": {
        "key": "intent_framer",
        "label": "Encuadre de intención",
        "role": "Prepara / resuelve la pregunta para retrieval (incluye memoria de sesión).",
        "llm_driven": False,
        "tools": [],
    },
    "corpus_fetcher": {
        "key": "corpus_fetcher",
        "label": "Recuperación de evidencia",
        "role": "Único nodo con acceso al retriever semántico del corpus Metropol.",
        "llm_driven": False,
        "tools": ["search_corpus"],
    },
    "grounded_composer": {
        "key": "grounded_composer",
        "label": "Síntesis grounded",
        "role": "Redacta la respuesta con citas sobre evidencia recuperada.",
        "llm_driven": True,
        "tools": [],
    },
    "source_guard": {
        "key": "source_guard",
        "label": "Validación de citas",
        "role": "Descarta citas que no corresponden a hits recuperados.",
        "llm_driven": False,
        "tools": [],
    },
    "escalation_gate": {
        "key": "escalation_gate",
        "label": "Gate de revisión humana",
        "role": "Pausa la corrida cuando hay razones de revisión.",
        "llm_driven": False,
        "tools": [],
    },
}


def agent_catalog() -> dict[str, Any]:
    """Return agents + effective knobs + domains for the console."""
    settings = get_settings()
    order = ("orchestrator", *FALLBACK_LADDER, "escalation_gate")
    agents = [_AGENT_META[key] for key in order if key in _AGENT_META]
    return {
        "agents": agents,
        "ladder": list(FALLBACK_LADDER),
        "domains": list(DOMAINS),
        "knobs": {
            "agentic_orchestrator_max_steps": settings.agentic_orchestrator_max_steps,
            "agentic_confidence_threshold": settings.agentic_confidence_threshold,
        },
    }
