# Proposal

## Why

Agentic pause/resume today uses an in-process `MemorySaver`. A Uvicorn reload drops every paused `thread_id`, so human review cannot continue after a restart. Production-shaped durability (same Postgres as pgvector) is the documented follow-up after live progress.

## What Changes

- Replace the default agentic checkpointer with a **Postgres** LangGraph saver on `DATABASE_URL` (same Compose Postgres as RAG).
- Open the saver at app startup (`setup()` idempotent); inject it via existing `get_checkpointer()` into `AgenticAnswerRunner`.
- Keep **MemorySaver** for tests / explicit offline flag.
- Exclude LangGraph `checkpoint*` tables from Alembic autogenerate when applicable.
- Update `AGENTS.md`: resume survives process restart; activity/progress log remains process-scoped.

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `agentic-answer`: Paused threads MUST remain resumable after API process restart when Postgres checkpointer is configured; document MemorySaver-only mode for tests.

## Non-goals

- Persisting the live-progress **activity log** (still in-process).
- Orchestrator / supervisor hub.
- Migrating the agentic runner or SQLAlchemy stack to async.
- Alembic migrations that own LangGraph checkpoint tables (`setup()` creates them).
- HTTP contract or frontend UI changes.

## Impact

- **Surface:** backend (docs caveat only on front if MemorySaver wording changes).
- **Backend:** `domain/graph/checkpointer.py`, `main` lifespan or equivalent wiring, `requirements.txt` (`langgraph-checkpoint-postgres`, pool if needed), Alembic `env.py` skip list, agentic tests, `AGENTS.md`.
- **APIs:** same start / progress / sync agentic / resume paths; durable resume behavior after restart.
- **Infra:** existing Postgres; no new Compose service.

## Practices check

- **Aligned:** checkpointer stays in `domain/graph/`; settings via `DATABASE_URL` / `get_settings()`; thin routers unchanged; deps in `requirements.txt`; tests keep isolated MemorySaver via `reset_checkpointer`.
- **Deviations:** prefer sync `PostgresSaver` vs course/peer `AsyncPostgresSaver` because the Metropol graph runner is sync + background threads; LangGraph tables via `setup()` not Alembic (same as course/peer).
- **Risks if ignored:** resumes still lost on reload; Alembic autogenerate proposing DROP of `checkpoints*`; feeding SQLAlchemy driver URLs into libpq.

## Graphify notes

- Hubs to extend: `checkpointer.py` (`get_checkpointer` / `reset_checkpointer`), `AgenticAnswerRunner` / `runner.py`, `answer_agentic` routes, `test_agentic_*`.
- Prefer extending `checkpointer.py` over a parallel saver module; runner already compiles with `get_checkpointer()`.
