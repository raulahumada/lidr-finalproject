# Design

## Context

See proposal.md — Why. Today `backend/app/domain/graph/checkpointer.py` exposes a process singleton `MemorySaver` via `get_checkpointer()` / `reset_checkpointer()`. Graphify shows `runner.py` imports that module and compiles the graph with it; agentic tests reset the saver between cases. Course/peer (`session_16`, lidr-master) use `AsyncPostgresSaver` + `AsyncConnectionPool` + idempotent `setup()` on the same Postgres as embeddings, with checkpoint tables owned by LangGraph (not Alembic).

Metropol’s agentic path is **sync** (`invoke` / `stream` in a background thread for live progress). There is no app lifespan yet (`create_app()` only wires CORS + router).

## Goals / Non-Goals

**Goals:**
- Durable LangGraph checkpoints for pause/resume on the existing Postgres.
- Same `get_checkpointer()` surface for `AgenticAnswerRunner` (no parallel island).
- Safe Alembic coexistence with LangGraph-owned tables.
- Tests stay fast and isolated with MemorySaver / reset.

**Non-Goals:**
- Durable activity/progress log (remains in-process; after reload, `/progress` may 404 while resume still works if paused).
- Rewriting the graph or runner to async solely to match course `AsyncPostgresSaver`.
- New HTTP endpoints or UI.

## Decisions

### 1. Extend `checkpointer.py` (Graphify hub)
**Choice:** Keep all saver selection, DSN normalization, and lifecycle helpers in `domain/graph/checkpointer.py`; runner continues to call `get_checkpointer()`.

**Alternatives:** New `foundation/persistence/checkpointer.py` — rejected; Graphify and current imports already center on `domain/graph/checkpointer.py`, and the saver is graph infra not RAG store.

### 2. Sync `PostgresSaver` + pool (conscious deviation from course)
**Choice:** Prefer sync `PostgresSaver` from `langgraph-checkpoint-postgres` with a sync `psycopg_pool.ConnectionPool`, matching the sync runner/thread model.

**Alternatives:**
- `AsyncPostgresSaver` + lifespan + async bridge — course-aligned but forces async/sync glue around every invoke/stream/resume; larger change than needed.
- Keep MemorySaver — fails the durability goal.

**Fallback at apply:** If the installed package version makes sync saver awkward, use the smallest async bridge that still avoids rewriting specialist nodes; document in tasks notes.

### 3. DSN from `DATABASE_URL`
**Choice:** `saver_conninfo()` strips SQLAlchemy driver tokens (`+psycopg`, `+asyncpg`) to a plain `postgresql://` libpq URL (course/peer pattern).

### 4. Startup `setup()` via lifespan
**Choice:** Add a FastAPI lifespan (or equivalent exit stack) in `main.py` / `create_app()` that opens the pool, runs `setup()`, and registers the saver before serving. Close pool on shutdown.

**Alternatives:** Lazy open on first `get_checkpointer()` — works but hides setup failures until first agentic call; lifespan makes boot fail-fast.

### 5. MemorySaver for tests / flag
**Choice:** Default to Postgres when `DATABASE_URL` is set; use MemorySaver when `AGENTIC_CHECKPOINTER=memory` (or equivalent) **or** when tests call `reset_checkpointer()` which forces a fresh MemorySaver. Unit/API tests keep using reset + TestClient without requiring Postgres for the existing suite. Optional marked integration test exercises durable path when DB is available.

### 6. Alembic ignore `checkpoint*`
**Choice:** In `alembic/env.py` `include_object`, skip tables named like LangGraph’s (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`, `checkpoint_migrations`) so autogenerate does not propose DROP/CREATE.

### Layer map (`docs/python-best-practices.md`)

| Piece | Layer |
|-------|--------|
| `checkpointer.py` | `domain/graph` (orchestration infra already there) |
| pool/DSN helpers | same module (thin; no new foundation store) |
| lifespan in `main` | composition root / app factory |
| routers | unchanged; still thin |

**Tension:** Course puts checkpointer under the same graph package and uses async; we keep the package home but stay sync. Acceptable deviation for current stack.

## Risks / Trade-offs

- [Sync vs async saver API drift] → Pin `langgraph-checkpoint-postgres`; verify import path in apply; fallback bridge documented.
- [Idle connections dropped during long human pause] → Use a connection pool with checkout validation (course rationale); avoid a single long-lived raw connection.
- [Activity log still process-scoped] → Document clearly; resume works after restart, live progress UI may need a fresh start or direct resume with known `thread_id`.
- [Alembic fights LangGraph tables] → `include_object` skip list.
- [Tests accidentally hit Postgres] → `reset_checkpointer()` / memory flag remains the test default path.

## Migration Plan

1. Add dependency; implement checkpointer + lifespan; skip Alembic tables.
2. Deploy with existing Postgres; first boot runs `setup()` and creates tables.
3. Rollback: set memory flag or revert module; checkpoint tables can remain unused.
4. No client migration; same `thread_id` / resume contract.

## Open Questions

None deferred — open questions from the draft are resolved in Decisions (flag + no health check for checkpoint tables in v1).
