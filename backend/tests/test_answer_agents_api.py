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
    composer = next(a for a in body["agents"] if a["key"] == "grounded_composer")
    assert composer["kind"] == "builtin"
    assert composer["mutable"] is False
    assert composer.get("prompt_preview")


def test_builtin_detail_and_immutable_mutations() -> None:
    client = TestClient(create_app())
    detail = client.get("/api/v1/answer/agents/grounded_composer")
    assert detail.status_code == 200
    assert detail.json()["mutable"] is False

    patch = client.patch(
        "/api/v1/answer/agents/orchestrator",
        json={"label": "nope"},
    )
    assert patch.status_code == 405

    delete = client.delete("/api/v1/answer/agents/orchestrator")
    assert delete.status_code == 405

    conflict = client.post(
        "/api/v1/answer/agents",
        json={
            "key": "corpus_fetcher",
            "label": "x",
            "role": "y",
            "system_prompt": "z",
        },
    )
    assert conflict.status_code == 409
