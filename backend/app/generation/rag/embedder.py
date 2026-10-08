"""OpenAI embedder for text-embedding-3-small."""

from __future__ import annotations

from openai import OpenAI

from app.generation.rag.constants import DEFAULT_EMBEDDING_MODEL


class OpenAIEmbedder:
    def __init__(self, client: OpenAI, model: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self._client = client
        self._model = model

    def embed_one(self, text: str) -> list[float]:
        response = self._client.embeddings.create(model=self._model, input=[text])
        return list(response.data[0].embedding)

    def embed_many(self, texts: list[str], *, batch_size: int = 64) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), batch_size):
            batch = texts[start : start + batch_size]
            response = self._client.embeddings.create(model=self._model, input=batch)
            by_index = {item.index: list(item.embedding) for item in response.data}
            vectors.extend(by_index[i] for i in range(len(batch)))
        return vectors
