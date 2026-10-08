from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4000)
    k: int = Field(default=5, ge=1, le=50)


class SearchHit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    chunk_id: int
    document_id: int
    chunk_type: str
    content: str
    score: float
    distance: float
    source_path: str
    document_type: str
    metadata: dict = Field(default_factory=dict)


class SearchResponse(BaseModel):
    query: str
    k: int
    search_time_ms: int
    results: list[SearchHit]
