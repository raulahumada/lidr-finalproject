# Tasks

## 1. Backend — persistence + API

- [x] 1.1 Add `AgentProfileRow` (customs only) + Alembic migration; verify upgrade/downgrade
- [x] 1.2 Implement `domain/graph/agent_store.py` (list/create/update/delete + reserved builtin keys); verify unit tests for 409/immutable builtins
- [x] 1.3 Enrich `catalog.py` to merge builtins + customs, Jinja `prompt_preview` for LLM builtins; verify GET catalog shape
- [x] 1.4 Extend `answer_agents` routes: GET detail, POST, PATCH, DELETE with correct status codes; verify TestClient cases

## 2. Backend — graph runtime

- [x] 2.1 Add `prompt_specialist` node (DB system prompt, bounded context, trace/side note); verify unit/smoke test with stub chat
- [x] 2.2 Wire orchestrator/build so enabled customs run after `corpus_fetcher` before `grounded_composer` under step budget; verify routing_history includes custom when enabled and skips when disabled
- [x] 2.3 Document API + Jinja-vs-DB prompt split in root `AGENTS.md`

## 3. Frontend — agents studio

- [x] 3.1 Extend `lib/api/agents.ts` for enriched catalog + CRUD client; verify TypeScript types
- [x] 3.2 Upgrade `/agents` UI: builtin read-only detail + prompt, custom create/edit/delete, ladder/flow section (Astryx); verify manual smoke notes in `frontend/AGENTS.md`
- [x] 3.3 Update `frontend/AGENTS.md` for studio behaviors

## 4. Integration

- [x] 4.1 Run `cd backend && .venv/bin/python -m pytest -q` and fix regressions
- [x] 4.2 Run `cd frontend && npx tsc --noEmit`
- [x] 4.3 Run `graphify update .` after code lands

## Workflow follow-up

- Archive after apply when ready
- `/commit-pr` when the user asks
