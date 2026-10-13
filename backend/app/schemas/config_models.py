"""HTTP contracts for runtime chat-model configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RoleModelView(BaseModel):
    effective: str
    default: str
    overridden: bool


class ModelsConfigResponse(BaseModel):
    models: dict[str, RoleModelView]
    available_models: list[str]
    embedding_model: str
    embedding_model_note: str = (
        "Embedding model is settings-only (.env); changing it would invalidate stored vectors."
    )


class ModelsConfigUpdateRequest(BaseModel):
    models: dict[str, str | None] = Field(
        ...,
        description="Role → model id, or null to clear the override",
        min_length=1,
    )
