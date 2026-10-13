from fastapi.testclient import TestClient

from app.main import create_app


def test_answer_agents_catalog() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/answer/agents")
    assert response.status_code == 200
    body = response.json()
    keys = {a["key"] for a in body["agents"]}
    assert "orchestrator" in keys
    assert "corpus_fetcher" in keys
    assert "escalation_gate" in keys
    assert "ventas" in body["domains"]
    assert "agentic_orchestrator_max_steps" in body["knobs"]
