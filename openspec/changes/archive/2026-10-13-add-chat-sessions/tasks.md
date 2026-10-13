# Tasks

## 1. Backend — persistence and session API

- [x] 1.1 Add SQLAlchemy model + Alembic migration for `conversation_sessions` (id, title, history JSON/JSONB, timestamps); verify `alembic upgrade head` succeeds against local Postgres
- [x] 1.2 Implement `SessionStore` under `generation/conversation/` (create/list/get/rename/delete/append_turn + auto-title); verify unit tests cover create, append, 404 paths without hitting routers
- [x] 1.3 Add Pydantic schemas + thin routes `POST/GET/PATCH/DELETE /answer/session*` and `GET /answer/sessions`; register in `api/router.py`; verify OpenAPI/`TestClient` CRUD smoke passes
- [x] 1.4 Document session vs thread in root `AGENTS.md`; verify the doc names the new endpoints

## 2. Backend — agentic session binding

- [x] 2.1 Extend agentic request schemas and sync/start handlers to accept optional `session_id` (404 if unknown before run); verify tests for missing/invalid/valid id
- [x] 2.2 On terminal completed/rejected/adjust outcomes (sync, background finish, resume), append history via `SessionStore` when bound; verify no append on pause/running and append after resume approve/reject
- [x] 2.3 Run `cd backend && .venv/bin/python -m pytest -q` (or focused agentic+session tests) and fix regressions

## 3. Frontend — sessions UI (Astryx)

- [x] 3.1 Add `lib/api/sessions.ts` (+ types) for session CRUD; verify typed calls against the new endpoints
- [x] 3.2 Pass optional `session_id` through `agentic.ts` start/run helpers; verify request body includes it when set
- [x] 3.3 Extend `/answer` with Astryx `ai-chat` patterns: session list, new chat, active session, `?session=` restore of history; verify create/switch/reload shows prior turns without raw layout divs
- [x] 3.4 Update `frontend/AGENTS.md` for sessions vs threads and deep link; verify docs match UI behavior

## 4. Integration / graph

- [x] 4.1 Manual smoke: create two sessions, ask in each, reload `?session=`, confirm histories distinct; pause+approve in one and confirm turn appended
- [x] 4.2 Run `graphify update .` after code lands

## Workflow follow-up

- Archive after apply (`/opsx-archive`) when ready
- Commit/PR via `/commit-pr-development` when the user asks
