# Tasks

## 1. Backend — runtime model config

- [x] 1.1 Add Settings allowlist (`available_chat_models` / `AVAILABLE_CHAT_MODELS`) and document in `backend/.env.example`; verify defaults include at least `gpt-4o-mini` and `gpt-4o`
- [x] 1.2 Implement `foundation/llm/runtime_config.py` (roles, effective/fallback, Redis hash, soft-fail reads, write → unavailable error); verify with unit tests using a fake/in-memory redis double
- [x] 1.3 Add Pydantic schemas + thin `GET/PUT /api/v1/config/models` router; wire in `api/router.py` and dependencies; verify 422/503/clear-null behaviors in pytest
- [x] 1.4 Make `ChatClient` (and sync answer / agentic composer / prompt_specialist call sites) use effective models per role at completion time; verify with a unit/integration test that a PUT changes the model string used on the next complete call (mock OpenAI)
- [x] 1.5 Document curl get/put and Redis caveat (CAG cache) in root `AGENTS.md`

## 2. Frontend — settings console

- [x] 2.1 Add typed client `frontend/app/lib/api/config.ts` for get/put models; verify `tsc` types
- [x] 2.2 Replace `/settings` stub with Astryx form (role selectors, clear-to-default, save, embedding read-only, error/success); verify 503 and success paths in UI logic
- [x] 2.3 Update `frontend/AGENTS.md` smoke for `/settings`; run `npx tsc --noEmit`

## 3. Integration check

- [x] 3.1 Smoke: Redis up → GET models → PUT composer override → agentic or answer still works; document skip if Redis/API missing
- [x] 3.2 Run `graphify update .` after code lands

## Workflow follow-up

- Sync/archive after apply
- Next planned: auth mínima
