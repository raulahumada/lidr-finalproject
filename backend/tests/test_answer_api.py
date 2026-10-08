from fastapi.testclient import TestClient

from app.main import create_app


def test_answer_503_without_openai_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    from app.config import get_settings
    from app import dependencies

    get_settings.cache_clear()
    dependencies.get_chunk_store.cache_clear()

    client = TestClient(create_app())
    response = client.post("/api/v1/answer", json={"question": "hola"})
    assert response.status_code == 503
