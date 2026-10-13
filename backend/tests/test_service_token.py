"""Service token middleware + boot policy."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.service_token import assert_service_token_boot_policy
from app.config import Settings, get_settings
from app.main import create_app


def _clear_settings_cache() -> None:
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_settings():
    _clear_settings_cache()
    yield
    _clear_settings_cache()


def test_open_mode_allows_unauthenticated_search(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_TOKEN", "")
    monkeypatch.setenv("APP_ENV", "development")
    _clear_settings_cache()
    app = create_app()
    # search may 503 without embeddings; must not be 401
    response = TestClient(app).post("/api/v1/search", json={"query": "x", "k": 1})
    assert response.status_code != 401


def test_configured_token_rejects_without_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_TOKEN", "secret-token")
    monkeypatch.setenv("APP_ENV", "development")
    _clear_settings_cache()
    app = create_app()
    response = TestClient(app).post("/api/v1/search", json={"query": "x", "k": 1})
    assert response.status_code == 401
    assert response.headers.get("www-authenticate", "").lower().startswith("bearer")


def test_configured_token_accepts_bearer(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_TOKEN", "secret-token")
    monkeypatch.setenv("APP_ENV", "development")
    _clear_settings_cache()
    app = create_app()
    response = TestClient(app).post(
        "/api/v1/search",
        json={"query": "x", "k": 1},
        headers={"Authorization": "Bearer secret-token"},
    )
    assert response.status_code != 401


def test_health_open_when_token_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_TOKEN", "secret-token")
    monkeypatch.setenv("APP_ENV", "development")
    _clear_settings_cache()
    app = create_app()
    response = TestClient(app).get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_production_empty_token_refuses_boot() -> None:
    settings = Settings(app_env="production", service_token="")
    with pytest.raises(RuntimeError, match="SERVICE_TOKEN"):
        assert_service_token_boot_policy(settings)


def test_production_with_token_allows_boot() -> None:
    settings = Settings(app_env="production", service_token="prod-secret")
    assert_service_token_boot_policy(settings)  # does not raise
