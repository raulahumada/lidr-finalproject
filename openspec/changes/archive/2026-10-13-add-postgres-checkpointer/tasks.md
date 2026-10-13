# Tasks

## 1. Dependencies and checkpointer module

- [x] 1.1 Add `langgraph-checkpoint-postgres` (and `psycopg-pool` if not already covered) to `backend/requirements.txt` with version floors; install into the venv and confirm `from langgraph.checkpoint.postgres import PostgresSaver` (or the package’s documented sync import) succeeds
- [x] 1.2 Rewrite `backend/app/domain/graph/checkpointer.py`: `saver_conninfo()` from `DATABASE_URL`, Postgres saver + pool when durable mode is on, MemorySaver when `AGENTIC_CHECKPOINTER=memory` / tests; keep `get_checkpointer()` / `reset_checkpointer()`; verify by importing the module and asserting memory mode returns a MemorySaver
- [x] 1.3 Add optional settings field(s) for checkpointer mode in `app/config.py` + document in `backend/.env.example`; verify `get_settings()` reads the flag without breaking existing env loads

## 2. App lifecycle and Alembic coexistence

- [x] 2.1 Wire FastAPI lifespan (or equivalent) in `create_app()` / `main.py` to open the durable saver, run idempotent `setup()`, and close the pool on shutdown; verify app boots with Postgres up (`uvicorn` or TestClient startup) without error when `DATABASE_URL` is set
- [x] 2.2 Update `alembic/env.py` to skip LangGraph `checkpoint*` tables in autogenerate `include_object`; verify by reading the skip list or running a dry autogenerate that does not propose those tables
- [x] 2.3 Ensure `AgenticAnswerRunner` still compiles against `get_checkpointer()` after lifespan init (no duplicate MemorySaver singleton fighting the pool); verify existing pause/resume unit path still works under memory/reset

## 3. Tests and docs

- [x] 3.1 Keep / adjust `test_agentic_graph.py`, `test_agentic_api.py`, and `test_agentic_progress_api.py` so they use MemorySaver via `reset_checkpointer()` (or env); verify `cd backend && .venv/bin/python -m pytest -q tests/test_agentic_*.py` passes
- [x] 3.2 Add a marked integration test (skip without DB) that pauses a thread, recreates checkpointer/app against the same DB, and resumes successfully; verify the test passes when Postgres is available and skips cleanly otherwise
- [x] 3.3 Update root `AGENTS.md` (and frontend caveat only if MemorySaver wording remains): durable resume after restart; activity/progress still process-scoped; verify docs mention both behaviors

## 4. Integration / graph refresh

- [x] 4.1 Manual smoke (optional if 3.2 covers it): with Compose Postgres healthy, start API, pause an agentic run, restart Uvicorn, resume with the same `thread_id`; verify HTTP 200 completed (or documented reject/adjust) rather than 404 solely due to restart
- [x] 4.2 Run `graphify update .` after code lands and confirm `checkpointer.py` / lifespan nodes refresh in the graph

## Workflow follow-up

- Archive change after apply + validate when ready (`/opsx-archive`)
- Commit/PR via `/commit-pr-development` when the user asks
