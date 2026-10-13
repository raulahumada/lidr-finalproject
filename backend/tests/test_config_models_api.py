"""HTTP tests for /api/v1/config/models."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.dependencies import get_runtime_model_config
from app.foundation.llm.chat import ChatClient
from app.foundation.llm.runtime_config import InMemoryRedisHash, RuntimeModelConfig
from app.main import app


def _settings() -> Settings:
    return Settings(
        chat_model="gpt-4o-mini",
        available_chat_models="gpt-4o-mini,gpt-4o",
        embedding_model="text-embedding-3-small",
    )


def test_get_models_snapshot() -> None:
    runtime = RuntimeModelConfig(InMemoryRedisHash(), _settings())
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_runtime_model_config] = lambda: runtime
    try:
        response = TestClient(app).get("/api/v1/config/models")
        assert response.status_code == 200
        body = response.json()
        assert set(body["models"]) == {"chat", "composer", "prompt_specialist"}
        assert body["models"]["chat"]["effective"] == "gpt-4o-mini"
        assert body["models"]["chat"]["overridden"] is False
        assert "gpt-4o" in body["available_models"]
        assert body["embedding_model"] == "text-embedding-3-small"
        assert "models" in body
        assert "embedding" not in body["models"]
    finally:
        app.dependency_overrides.clear()


def test_put_rejects_unknown_model() -> None:
    runtime = RuntimeModelConfig(InMemoryRedisHash(), _settings())
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_runtime_model_config] = lambda: runtime
    try:
        response = TestClient(app).put(
            "/api/v1/config/models",
            json={"models": {"composer": "gpt-not-real"}},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_put_and_clear_override() -> None:
    runtime = RuntimeModelConfig(InMemoryRedisHash(), _settings())
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_runtime_model_config] = lambda: runtime
    try:
        client = TestClient(app)
        put = client.put(
            "/api/v1/config/models",
            json={"models": {"composer": "gpt-4o"}},
        )
        assert put.status_code == 200
        assert put.json()["models"]["composer"]["effective"] == "gpt-4o"
        assert put.json()["models"]["composer"]["overridden"] is True

        clear = client.put(
            "/api/v1/config/models",
            json={"models": {"composer": None}},
        )
        assert clear.status_code == 200
        assert clear.json()["models"]["composer"]["overridden"] is False
        assert clear.json()["models"]["composer"]["effective"] == "gpt-4o-mini"
    finally:
        app.dependency_overrides.clear()


def test_put_503_when_redis_unavailable() -> None:
    runtime = RuntimeModelConfig(None, _settings())
    app.dependency_overrides[get_settings] = _settings
    app.dependency_overrides[get_runtime_model_config] = lambda: runtime
    try:
        response = TestClient(app).put(
            "/api/v1/config/models",
            json={"models": {"chat": "gpt-4o"}},
        )
        assert response.status_code == 503
    finally:
        app.dependency_overrides.clear()


class _RecordingOpenAI:
    def __init__(self) -> None:
        self.models: list[str] = []

        class _Completions:
            def __init__(self, outer: _RecordingOpenAI) -> None:
                self._outer = outer

            def create(self, **kwargs: object) -> object:
                self._outer.models.append(str(kwargs.get("model")))

                class _Msg:
                    content = '{"answer":"ok"}'

                class _Choice:
                    message = _Msg()

                class _Resp:
                    choices = [_Choice()]

                return _Resp()

        class _Chat:
            def __init__(self, outer: _RecordingOpenAI) -> None:
                self.completions = _Completions(outer)

        self.chat = _Chat(self)


def test_chat_client_uses_role_override_at_call_time() -> None:
    store = InMemoryRedisHash()
    runtime = RuntimeModelConfig(store, _settings())
    client = _RecordingOpenAI()
    chat = ChatClient(client, model="gpt-4o-mini", runtime=runtime)  # type: ignore[arg-type]
    chat.complete_json(system="s", user="u", role="composer")
    assert client.models[-1] == "gpt-4o-mini"
    runtime.set("composer", "gpt-4o")
    chat.complete_json(system="s", user="u", role="composer")
    assert client.models[-1] == "gpt-4o"
