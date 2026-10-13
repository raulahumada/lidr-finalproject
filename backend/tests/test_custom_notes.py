from __future__ import annotations

from app.domain.graph.activity import GraphActivityLog
from app.domain.graph.runner import AgenticAnswerRunner


def test_activity_log_accumulates_custom_notes() -> None:
    log = GraphActivityLog()
    log.start("t1", question="q")
    log.extend_custom_notes(
        "t1",
        [{"key": "risk_advisor", "note": "cuidado con mora"}],
    )
    run = log.read("t1")
    assert run is not None
    assert run.custom_notes == [
        {"key": "risk_advisor", "note": "cuidado con mora"}
    ]


def test_runner_maps_custom_notes_on_response() -> None:
    notes = AgenticAnswerRunner._custom_notes(
        [{"key": "risk_advisor", "note": "revisá handoff"}]
    )
    assert len(notes) == 1
    assert notes[0].key == "risk_advisor"
    assert "handoff" in notes[0].note


def test_to_response_includes_custom_notes() -> None:
    # Minimal stub: call private mapper via a thin constructed response path
    response = AgenticAnswerRunner._to_response(
        AgenticAnswerRunner.__new__(AgenticAnswerRunner),
        "thread-1",
        {
            "question": "hola",
            "status": "completed",
            "custom_notes": [{"key": "risk_advisor", "note": "nota demo"}],
            "agent_trace": [],
            "routing_history": [],
            "citations": [],
        },
        resolved_k=5,
    )
    assert response.custom_notes[0].key == "risk_advisor"
    assert response.custom_notes[0].note == "nota demo"
