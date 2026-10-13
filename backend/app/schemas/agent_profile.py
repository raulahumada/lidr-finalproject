"""Request/response schemas for custom agent profiles."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentProfileCreate(BaseModel):
    key: str = Field(..., min_length=2, max_length=64)
    label: str = Field(..., min_length=1, max_length=120)
    role: str = Field(..., min_length=1, max_length=4000)
    system_prompt: str = Field(..., min_length=1, max_length=50000)
    enabled: bool = True


class AgentProfileUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=120)
    role: str | None = Field(default=None, min_length=1, max_length=4000)
    system_prompt: str | None = Field(default=None, min_length=1, max_length=50000)
    enabled: bool | None = None


class AgentProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str
    role: str
    system_prompt: str
    enabled: bool
    kind: str = "custom"
    llm_driven: bool = True
    tools: list[str] = Field(default_factory=list)
    mutable: bool = True
    prompt_preview: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
