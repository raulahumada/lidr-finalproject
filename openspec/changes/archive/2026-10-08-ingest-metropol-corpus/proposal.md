# Proposal

## Why

`POST /api/v1/search` ya funciona, pero el índice solo tiene un fixture de demo. Sin ingestar el corpus Metropol Fintech desde el filesystem local, el retrieval no sirve dominio real (omnicanalidad, ventas, cobranzas, Tenela).

## What Changes

- Añadir pipeline de **ingesta batch** bajo `backend/app/ingestion/` (loader + parsers por formato + orquestación CLI).
- Settings `CORPUS_ROOT` y allowlist de extensiones (default `pdf,docx,txt,md`).
- Reutilizar embedder + `ChunkStore` existentes para persistir en `documents`/`chunks`.
- Idempotencia por `source_path` (skip por defecto; `--force` re-ingiere).
- Dependencias de parseo (`pypdf`, `python-docx`) y tests de parsers/skip/idempotencia.
- Documentar en `AGENTS.md` cómo apuntar el path y correr el CLI.

## Non-goals

- xlsx / pptx / png / vsdx / mp4 / zip (skip)
- OCR, transcripción de video
- HTTP ingest API, UI, jobs table / DataCatalog completo del curso
- PII pipeline, `/answer`, agentes, HNSW
- Commitear archivos del corpus

## Capabilities

### New Capabilities
- `corpus-ingest`: Batch ingest from a local `CORPUS_ROOT` with format allowlist, parsers per extension, chunk+embed+persist into the existing RAG store, and a documented CLI summary.

### Modified Capabilities
- (ninguna — reutiliza `rag-chunks` / `semantic-search` sin cambiar sus requisitos)

## Impact

- **Surface:** backend.
- **Paths:** `backend/app/ingestion/`, `backend/app/generation/rag/` (chunking helper), `backend/app/config.py`, `backend/.env.example`, `backend/requirements.txt`, tests, `AGENTS.md`.
- **APIs:** sin endpoints nuevos (CLI only).
- **Deps:** pypdf, python-docx (+ existentes openai/sqlalchemy).
- **Course ref:** `app/ingestion` ParserRegistry / filesystem loader shape from `session_16`; domain = Metropol.

## Practices check

- **Aligned:**
  - Capas ingestion → generation/rag + foundation/persistence; no SQL/LLM en routers
  - Settings vía `get_settings()`; path por env
  - Reuso de store/embedder; deps con `>=` en `requirements.txt`
- **Deviations:**
  - Sin DataCatalog/jobs del curso en v1. Motivo: un root local + CLI alcanza para el primer slice.
  - Sin xlsx en v1. Motivo: priorizar docs narrativos; mismo deferral que el registry default del curso.
- **Risks if ignored:**
  - Indexar media (mp4/png) → costo y ruido
  - Corpus en git → datos de cliente
  - Ingest en HTTP handlers → mezcla de capas
