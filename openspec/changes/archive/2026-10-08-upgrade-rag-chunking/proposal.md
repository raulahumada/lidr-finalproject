# Proposal

## Why

El corpus Metropol ya está indexado, pero el chunker actual (párrafo / fixed-size) es el baseline débil del artículo de sesión 7: mezcla o rompe ideas y limita la calidad de `/search`. Hay que adoptar el default medido del curso (recursive) y estructura donde aplique, **antes** de `/answer`.

## What Changes

- Reemplazar el chunker simple por API tipada con **normalización de texto** + estrategia **recursive** (~512 tokens, overlap ~10–20%).
- Chunking **Markdown por headers** para `.md`; recursive (+ metadata de sección barata si aplica) para txt/pdf/docx.
- Usar `langchain-text-splitters` (+ tiktoken) como en el curso.
- Cablear el orchestrator de ingest al nuevo chunker; documentar re-ingest `--force`.
- Tests unitarios del splitter; verificación con re-ingest Metropol + smoke search.

## Non-goals

- Semantic / LLM / late / agentic / Contextual Retrieval / parent-child
- Cambio de embeddings, HNSW, `/answer`, UI
- Cambiar librerías de parse PDF/DOCX

## Capabilities

### New Capabilities
- `rag-chunking`: Strategies and normalization used to split extracted corpus text into embeddable chunks (recursive default, markdown structural), independent of filesystem walk.

### Modified Capabilities
- (ninguna requisito-nivel en `corpus-ingest` — el walk/allowlist no cambia; solo qué texto llega a embed)

## Impact

- **Surface:** backend.
- **Paths:** `backend/app/generation/rag/chunking*`, `backend/app/ingestion/orchestrator.py`, `requirements.txt`, tests, `AGENTS.md`.
- **APIs:** sin cambios de contrato HTTP.
- **Ops:** re-ingest local con `--force` para regenerar embeddings.
- **Course ref:** `RecursiveChunker` / session-07 guidance.

## Practices check

- **Aligned:** chunking en `generation/rag`; ingestion orquesta; tests del splitter.
- **Deviations:** dependencia LangChain **solo** text-splitters (no stack RAG completo). Motivo: mismo default del curso. Sin golden-set eval formal en este slice.
- **Risks if ignored:** retrieval difuso; tentación de saltar a semantic sin medir.
