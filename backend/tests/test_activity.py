from __future__ import annotations

from app.domain.graph.activity import GraphActivityLog, describe_node


def test_describe_known_metropol_nodes() -> None:
    [intent] = describe_node("intent_framer", {"framed_query": "hola", "agent_trace": []})
    assert intent["node"] == "intent_framer"
    assert "Encuadre" in intent["label"]

    [hub] = describe_node(
        "orchestrator",
        {"next_agent": "corpus_fetcher", "route_reason": "siguiente en escalera"},
    )
    assert hub["node"] == "orchestrator"
    assert "Orquestador" in hub["label"]
    assert "corpus_fetcher" in hub["message"]
    assert "escalera" in hub["message"]

    [corpus] = describe_node(
        "corpus_fetcher",
        {"hits": [{"chunk_id": 1}, {"chunk_id": 2}], "no_evidence": False},
    )
    assert "2 chunk" in corpus["message"]

    [guard] = describe_node("source_guard", {"citations_valid": True})
    assert "respaldadas" in guard["message"]


def test_describe_unknown_node_degrades() -> None:
    [entry] = describe_node("future_node", {"whatever": object()})
    assert entry["node"] == "future_node"
    assert entry["message"]


def test_describe_uses_agent_trace_summary() -> None:
    [entry] = describe_node(
        "grounded_composer",
        {
            "agent_trace": [{"node": "grounded_composer", "summary": "composed draft"}],
            "answer": "x" * 10,
        },
    )
    assert entry["message"] == "composed draft"


def test_activity_log_lifecycle() -> None:
    log = GraphActivityLog()
    log.start("t1", question="q")
    log.append("t1", "intent_framer", "Encuadre", "ok")
    assert log.read("t1") is not None
    assert log.read("t1").status == "running"  # type: ignore[union-attr]
    log.finish("t1", "completed", result={"answer": "a"})
    run = log.read("t1")
    assert run is not None
    assert run.status == "completed"
    assert run.result == {"answer": "a"}
    assert log.read("missing") is None
