from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Entrega LiDR API"
    app_env: str = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    # Host-run API → Compose Postgres on localhost:5432.
    # Set DATABASE_URL in backend/.env (see backend/.env.example); no secrets in code.
    database_url: str = ""
    # Embeddings (text-embedding-3-small, 1536-d). Empty key → search/answer return 503.
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    # Local Metropol corpus (absolute path). Empty → ingest CLI refuses to run.
    corpus_root: str = ""
    corpus_extensions: str = "pdf,docx,txt,md"
    # Response CAG (Redis Stack). Soft-fail if unreachable.
    redis_url: str = "redis://localhost:6379"
    answer_cache_ttl_seconds: int = 86400
    semantic_cache_threshold: float = 0.92
    semantic_cache_log_only: bool = True
    answer_prompt_version: str = "v2"
    answer_default_k: int = 5
    answer_context_max_tokens: int = 3500
    knowledge_pack_max_tokens: int = 2048

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def embeddings_configured(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def corpus_extensions_list(self) -> list[str]:
        return [
            ext.strip().lstrip(".").lower()
            for ext in self.corpus_extensions.split(",")
            if ext.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
