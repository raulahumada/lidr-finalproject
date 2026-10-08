# Proposal

## Why

`POST /search` recovers Metropol chunks but does not answer questions. The next product slice needs grounded generation with citations, plus both Cache-Augmented Generation styles: a curated knowledge preload (peer lidr-master) and exact/semantic response caches (course `generation/cag/`).

## What Changes

- Add `POST /api/v1/answer` (question → answer + citations + `cached` flag).
- Add **Knowledge CAG**: token-measured Metropol pack injected into Jinja `system` prompt (fail if over ceiling; never silent truncate).
- Add **Response CAG**: Redis exact (SHA-256) + Redis Stack semantic caches around generation.
- Add Jinja prompts `answer/v1/{system,user}.j2`, thin LLM chat wrapper, domain conductor wiring CAG → RAG → LLM.
- Add Redis Stack to local Compose; settings + `.env.example` + `AGENTS.md` curl docs.
- Tests for cache hit/miss, no-evidence path, and API contract.

## Capabilities

### New Capabilities
- `rag-answer`: Grounded Q&A API over the Metropol corpus (retrieve → generate → cite).
- `response-cag`: Exact and semantic caches of generated answers (course CAG).
- `knowledge-cag`: Curated preloadable context with hard token ceiling (peer Knowledge CAG).

### Modified Capabilities
- (none — `semantic-search` / `rag-chunks` requirements unchanged; answer reuses them)

## Impact

- **Surface:** backend only.
- **Code:** `generation/cag/`, `foundation/prompts/`, `foundation/llm/`, `domain/answer_service.py`, `api/routes/answer.py`, schemas, config, deps, Compose Redis Stack.
- **Ops:** local Redis Stack; `OPENAI_API_KEY` required for miss path (503 if missing).
- **Out of scope:** agents/LangGraph, frontend chat, full guardrails suite, xlsx ingest.

## Practices check

- **Aligned:** thin routers; `get_settings()`; request/response schemas; layers (`foundation` / `generation` / `domain` conductor); deps with version floors; secrets via env.
- **Deviations:** Redis Stack (not alpine) for semantic index — same as course; Knowledge CAG preload lives outside `generation/cag/` (that package = response caches); minimal OpenAI chat wrapper (no Instructor/LiteLLM yet).
- **Risks if ignored:** silent pack truncation; caching failed/empty answers; cross-imports between `cag` and `rag`.
