# Proposal: add-ingest-console

## Why

Corpus ingest today is CLI-only (`python -m app.ingestion.run_ingest`). Cristian’s console exposes index runs from the UI; operators here still need a terminal to refresh Metropol chunks. Closing that gap unlocks demos without leaving the AppShell and bridges the Graphify-confirmed hole between `run_ingest` and the API router.

## What Changes

- Backend HTTP surface under `/api/v1/ingest`: start a run (202 + `run_id`), poll status/summary, read corpus stats
- In-process job registry (single concurrent run; 409 if busy); reuses existing `run_ingest` orchestrator
- Frontend `/ingest` console (Astryx): stats, force toggle, start + poll, summary → CTA to `/search`
- SideNav + home CTA; docs in `AGENTS.md` / `frontend/AGENTS.md`
- CLI remains supported; no **BREAKING** API removals

## Non-goals

- Browser file upload or HTTP override of `CORPUS_ROOT`
- Durable Postgres job table / DataCatalog multi-source
- Auth, AI settings / model router
- New parsers, chunking, or embedding model changes from this UI

## Capabilities

### New Capabilities

- `ingest-console-ui`: operator UI to inspect corpus stats and trigger/poll Metropol ingest runs

### Modified Capabilities

- `corpus-ingest`: add HTTP start/poll/stats requirements alongside the existing CLI contract (orchestrator behavior unchanged)

## Impact

- **Surface:** both (`backend/` + `frontend/`)
- **Backend:** `api/routes/ingest.py`, `schemas/ingest.py`, job registry, `ChunkStore` stats helper, router registration, tests, root `AGENTS.md`
- **Frontend:** `/ingest` page, `lib/api/ingest.ts`, SideNav + home CTA, `frontend/AGENTS.md`
- **API:** new `/api/v1/ingest/*` (additive)
- **Course ref:** thin router + BackgroundTasks pattern from `session_16` `api/ingestion.py` / `corpus_index.py` (not copied)

### Graphify notes

- Hubs: `ingestion/orchestrator.run_ingest`, `IngestSummary`, `ChunkStore`, CLI `run_ingest.py`, consumer `routes/search.py`
- Gap: no directed path `run_ingest` → `api_router` today — this change adds that bridge without inventing a parallel ingest pipeline

## Practices check

- **Aligned:** thin FastAPI router; business logic stays in `ingestion/orchestrator`; Pydantic schemas; `get_settings()`; composition via dependencies; reuse foundation store + rag embedder
- **Deviations:** in-process jobs (not course `JobsRepository`/Alembic) — local demo + parity with agentic activity log; no DataCatalog — single Metropol `CORPUS_ROOT`; no HTTP `root` override — avoids arbitrary filesystem reads pre-auth
- **Risks if ignored:** parsers in the router; concurrent double-embeds; path override without auth
