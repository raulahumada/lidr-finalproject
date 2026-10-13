"""Thin HTTP layer for runtime chat-model overrides."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import Settings, get_settings
from app.dependencies import get_runtime_model_config
from app.foundation.llm.runtime_config import (
    CHAT_ROLES,
    RuntimeConfigUnavailable,
    RuntimeModelConfig,
)
from app.schemas.config_models import (
    ModelsConfigResponse,
    ModelsConfigUpdateRequest,
    RoleModelView,
)

router = APIRouter(prefix="/config", tags=["config"])


def _payload(runtime: RuntimeModelConfig, settings: Settings) -> ModelsConfigResponse:
    snap = runtime.snapshot()
    return ModelsConfigResponse(
        models={
            role: RoleModelView(
                effective=str(entry["effective"]),
                default=str(entry["default"]),
                overridden=bool(entry["overridden"]),
            )
            for role, entry in snap.items()
        },
        available_models=list(settings.available_chat_models_list),
        embedding_model=settings.embedding_model,
    )


@router.get("/models", response_model=ModelsConfigResponse)
def get_models(
    settings: Settings = Depends(get_settings),
    runtime: RuntimeModelConfig = Depends(get_runtime_model_config),
) -> ModelsConfigResponse:
    return _payload(runtime, settings)


@router.put("/models", response_model=ModelsConfigResponse)
def update_models(
    request: ModelsConfigUpdateRequest,
    settings: Settings = Depends(get_settings),
    runtime: RuntimeModelConfig = Depends(get_runtime_model_config),
) -> ModelsConfigResponse:
    allowlist = set(settings.available_chat_models_list)
    for role, value in request.models.items():
        if role not in CHAT_ROLES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unknown role: {role}",
            )
        if value is not None and value not in allowlist:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Model {value!r} is not in AVAILABLE_CHAT_MODELS",
            )
    try:
        runtime.apply_updates(request.models)
    except RuntimeConfigUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Runtime model config unavailable: {exc}",
        ) from exc
    return _payload(runtime, settings)
