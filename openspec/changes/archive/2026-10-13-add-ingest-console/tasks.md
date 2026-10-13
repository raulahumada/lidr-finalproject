# Tasks

## 1. Backend — HTTP ingest surface

- [x] 1.1 Add Pydantic schemas for ingest run request/response, run status + summary, and stats (`app/schemas/ingest.py`); verify OpenAPI field shapes match the delta `corpus-ingest` requirements
- [x] 1.2 Add in-process job registry (`app/ingestion/jobs.py` or equivalent) with create / mark running / complete / fail / get and single-active-run guard; verify with unit tests for 409-busy semantics (no OpenAI)
- [x] 1.3 Add `ChunkStore` (or thin helper) document/chunk count stats used by `GET /ingest/stats`; verify counts against a temp session fixture
- [x] 1.4 Implement thin router `app/api/routes/ingest.py`: `POST /ingest/runs` (202, 503, 409), `GET /ingest/runs/{run_id}` (summary/404), `GET /ingest/stats`; wire into `api/router.py` and dependencies so background work calls existing `run_ingest` (no parsers in the route); verify with pytest (mock embedder + tmp corpus)
- [x] 1.5 Document HTTP curl examples next to the CLI in root `AGENTS.md`; verify the documented paths match the router prefix

## 2. Frontend — ingest console

- [x] 2.1 Add typed client `frontend/app/lib/api/ingest.ts` for stats / start / poll; verify TypeScript types compile against expected JSON shapes
- [x] 2.2 Scaffold `/ingest` via Astryx workflow and implement stats + force toggle + start/poll + summary/errors + CTA to `/search` (no ad-hoc `<div>` layout); verify page renders and handles 503/409 states
- [x] 2.3 Wire AppShell SideNav entry and home CTA to `/ingest`; verify navigation from shell and `/`
- [x] 2.4 Update `frontend/AGENTS.md` smoke steps for `/ingest`; run `npx tsc --noEmit` and fix any new errors

## 3. Integration check

- [x] 3.1 Smoke locally (or document skipped if env missing): start run via UI or curl → poll → stats change → `/search` still works; verify no regression on CLI `python -m app.ingestion.run_ingest --help`
- [x] 3.2 Run `graphify update .` after code lands so the graph links ingest routes to the orchestrator

## Workflow follow-up

- Sync/archive OpenSpec change after apply + review
- Next planned prespecs (not this change): AI settings / model router, then auth
