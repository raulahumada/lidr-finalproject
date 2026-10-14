"""HTTP contracts for LLM usage summary."""

from typing import Literal

from pydantic import BaseModel, Field

UsagePurpose = Literal["answer", "grounded_composer", "prompt_specialist"]


class TokenUsage(BaseModel):
    """Provider-reported (or zeroed) token counts for one completion / response."""

    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    reported: bool = False


class UsageByModel(BaseModel):
    model: str
    calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)


class UsageSummaryResponse(BaseModel):
    total_calls: int = Field(ge=0)
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    by_model: list[UsageByModel] = Field(default_factory=list)
