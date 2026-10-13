"""Wire the Metropol agentic answer graph (star + orchestrator hub)."""

from __future__ import annotations

import logging

from langgraph.graph import END, START, StateGraph

from app.domain.graph.agents import (
    corpus_fetcher,
    grounded_composer,
    intent_framer,
    source_guard,
)
from app.domain.graph.gate import escalation_gate
from app.domain.graph.orchestrator import FALLBACK_LADDER, orchestrator
from app.domain.graph.state import AgenticAnswerState

log = logging.getLogger(__name__)

AGENT_NODES = {
    "intent_framer": intent_framer,
    "corpus_fetcher": corpus_fetcher,
    "grounded_composer": grounded_composer,
    "source_guard": source_guard,
}


def build_agentic_answer_graph(checkpointer=None):
    builder = StateGraph(AgenticAnswerState)

    builder.add_node(
        "orchestrator",
        orchestrator,
        destinations=(*FALLBACK_LADDER, "escalation_gate"),
    )
    for name, fn in AGENT_NODES.items():
        builder.add_node(name, fn)
    builder.add_node("escalation_gate", escalation_gate)

    builder.add_edge(START, "orchestrator")
    for name in AGENT_NODES:
        builder.add_edge(name, "orchestrator")
    builder.add_edge("escalation_gate", END)

    compiled = builder.compile(checkpointer=checkpointer)
    log.info("agentic_answer_graph_built topology=star agents=%s", list(AGENT_NODES))
    return compiled
