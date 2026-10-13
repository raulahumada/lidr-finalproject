# Proposal

## Why

The Metropol answer chat is a single in-memory thread: reload or a second conversation loses context. Operators need durable multi-session history (like Cristian’s console) so several chats can exist in parallel and survive F5.

## What Changes

- Persist conversation sessions in Postgres with a durable `history` transcript.
- Expose session CRUD: create, list, get, rename, delete (`/answer/session*` + `/answer/sessions`).
- Accept optional `session_id` on agentic start (and sync agentic); append turns on terminal completed / resume outcomes (including reject, with status).
- Extend `/answer` UI (Astryx `ai-chat` patterns): session list, new chat, `?session=` restore — without scaffolding a new app route.

## Capabilities

### New Capabilities

- `chat-sessions`: Durable conversation sessions with list/create/open/rename/delete and a transcript of closed turns, distinct from LangGraph `thread_id`.

### Modified Capabilities

- `agentic-answer`: Optional `session_id` on agentic submit paths; append history when a run reaches a terminal human-facing outcome.
- `agentic-live-progress`: Start accepts optional `session_id`; background completion still appends via the same session rules.
- `agentic-chat-ui`: Multi-session chrome on `/answer` (list, new chat, deep link restore) while keeping live progress + human gate.

## Non-goals

- Cross-turn RAG memory (facts / anchors / resolved question in the LLM prompt).
- Auth / per-owner session isolation.
- Persisting live-progress activity logs.
- Orchestrator / supervisor.
- New frontend route from `astryx template ai-chat` scaffold path — evolve existing `/answer`.

## Impact

- **Surface:** both.
- **Backend:** Alembic model/store, session routes/schemas, agentic wiring, tests, `AGENTS.md`.
- **Frontend:** `answer/page.tsx`, session API client, `agentic.ts` `session_id`, `frontend/AGENTS.md`.
- **APIs:** new session endpoints; additive optional field on agentic start/sync.

## Practices check

- **Aligned:** thin routers; store under `generation/conversation/` (or foundation persistence + thin store); Pydantic schemas; Alembic; composition in `dependencies`; no SQL in routes.
- **Deviations:** single-tenant (no `owner_id`); `history` as JSONB for v1 (peer-aligned simplicity vs normalized turn table).
- **Risks if ignored:** conflating session with checkpointer `thread_id`; client-minted ids; UI-only localStorage without server transcript.

## Graphify notes

- Extend hubs: `answer/page.tsx`, `agentic.ts`, `AgenticAnswerRunner` / `answer_agentic`, persistence (`get_session_factory`).
- New island: conversation session store + routes (expected); do not store transcripts in LangGraph checkpoints.
