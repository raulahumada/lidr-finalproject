# Tasks

## 1. Backend — expose custom_notes

- [x] 1.1 Add `CustomAgentNote` + `custom_notes` on `AgenticAnswerResponse` and `AgenticProgressResponse`; verify schema imports
- [x] 1.2 Map `state["custom_notes"]` in runner `_to_response` and progress assembly; verify unit/API test with stubbed notes
- [x] 1.3 Note field briefly in root `AGENTS.md` (agentic progress/response)

## 2. Frontend — chat surface

- [x] 2.1 Extend `lib/api/agentic.ts` types + `progressToAnswer` for `custom_notes`
- [x] 2.2 Show notes on `/answer` (live + terminal) with Astryx List/Banner; verify smoke note in `frontend/AGENTS.md`
- [x] 2.3 Update `frontend/AGENTS.md`

## 3. Integration

- [x] 3.1 `cd backend && .venv/bin/python -m pytest -q`
- [x] 3.2 `cd frontend && npx tsc --noEmit`
- [x] 3.3 `graphify update .`

## Workflow follow-up

- Archive after apply when ready
- `/commit-pr` when the user asks
