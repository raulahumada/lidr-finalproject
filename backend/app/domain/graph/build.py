"""Wire the fixed Metropol agentic answer pipeline."""

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
from app.domain.graph.state import AgenticAnswerState

log = logging.getLogger(__name__)


def build_agentic_answer_graph(checkpointer=None):
    builder = StateGraph(AgenticAnswerState)
    builder.add_node("intent_framer", intent_framer)
    builder.add_node("corpus_fetcher", corpus_fetcher)
    builder.add_node("grounded_composer", grounded_composer)
    builder.add_node("source_guard", source_guard)
    builder.add_node("escalation_gate", escalation_gate)

    builder.add_edge(START, "intent_framer")
    builder.add_edge("intent_framer", "corpus_fetcher")
    builder.add_edge("corpus_fetcher", "grounded_composer")
    builder.add_edge("grounded_composer", "source_guard")
    builder.add_edge("source_guard", "escalation_gate")
    builder.add_edge("escalation_gate", END)

    compiled = builder.compile(checkpointer=checkpointer)
    log.info("agentic_answer_graph_built")
    return compiled
