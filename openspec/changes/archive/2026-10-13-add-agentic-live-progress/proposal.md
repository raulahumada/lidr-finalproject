# Proposal

## Why

The agentic chat UI waits on a blocking `POST /answer/agentic`, so operators only see a spinner until the whole graph finishes. Cristian and the course use start + progress polling to narrate specialist nodes while the run is live. We need that live progress without token streaming.

## What Changes

- Add `POST /api/v1/answer/agentic/start` (HTTP 202 + `thread_id`) and `GET /api/v1/answer/agentic/{thread_id}/progress`.
- Add an in-process activity log fed by `graph.stream(..., stream_mode="updates")` in a background thread.
- Switch the `/answer` chat hot path to start + poll (~1.2s) and animate agent steps via Astryx `ChatToolCalls`.
- Keep sync `POST /answer/agentic` and resume unchanged.

## Capabilities

### New Capabilities
- `agentic-live-progress`: Background agentic runs with narrated per-node activity, progress polling, and console UI that animates specialist steps while a run is live.

### Modified Capabilities
- `agentic-answer`: Add start/progress endpoints alongside the existing sync agentic API (requirements additive).

## Non-goals

- LLM token streaming
- Redis/Postgres activity store or Postgres checkpointer
- Peer session memory / retrieval filters / live-flow shadcn panel
- Changing sync `POST /answer/agentic` behavior

## Impact

- **Surface:** both (backend API + frontend chat).
- **Backend:** `domain/graph/activity.py`, runner background stream, routes/schemas/deps, tests, `AGENTS.md`.
- **Frontend:** `lib/api/agentic.ts`, `app/answer/page.tsx`, `frontend/AGENTS.md`.

## Practices check

- **Aligned:** thin routers; graph/activity in `domain/`; schemas for contracts; settings via `get_settings()`; tests for start/progress.
- **Deviations:** in-process activity log + `threading.Thread` (sync stack) instead of peer `asyncio` + `astream`; MemorySaver still process-scoped. Follow-ups documented.
- **Risks if ignored:** blocking the event loop with sync stream in-request; GC of background threads mid-run; treating progress 404 as empty success.

## Graphify notes

- Extend hubs: `AgenticAnswerRunner`, `answer_agentic` routes, `agentic.ts`, `answer/page.tsx`.
- New island: `domain/graph/activity.py` (expected), wired via runner + deps.
