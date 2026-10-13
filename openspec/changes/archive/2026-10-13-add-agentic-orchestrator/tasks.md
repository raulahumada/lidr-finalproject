# Tasks

## 1. Backend — orchestrator graph

- [x] 1.1 Add `agentic_orchestrator_max_steps` to Settings + `.env.example`; verify `get_settings()` exposes it
- [x] 1.2 Implement `domain/graph/orchestrator.py` (legal ladder, step budget, `routing_history` updates, `Command(goto)`); verify unit tests for ladder order, illegal override, budget exhaust
- [x] 1.3 Extend `AgenticAnswerState` with `domain`, `routing_history`, `supervisor_steps` / orchestrator step counter; verify typing compiles with graph
- [x] 1.4 Rewire `build_agentic_answer_graph` to star topology (orchestrator hub + specialist return edges + gate); verify graph smoke / agentic tests still pass happy path
- [x] 1.5 Implement lightweight domain detect + optional request override (422 if invalid); wire into runner initial state and response/progress payloads; verify auto + override + 422 tests

## 2. Backend — catalog API

- [x] 2.1 Add `domain/graph/catalog.py` + `GET /api/v1/answer/agents` (and optional knobs echo); register router; verify TestClient returns orchestrator + specialists
- [x] 2.2 Update activity `describe_node` for orchestrator; verify progress activity includes hub steps in a focused test
- [x] 2.3 Document orchestrator vs pipeline vs domain tag in root `AGENTS.md`; verify docs name catalog endpoint and env knob

## 3. Frontend — chat + agents console

- [x] 3.1 Extend agentic API types/client for `domain`, `routing_history`, catalog fetch; verify TypeScript build
- [x] 3.2 Update `/answer` UI: domain select (auto|…) on send, domain chip + routing visibility in progress/trace (Astryx); verify manual smoke checklist in AGENTS or frontend AGENTS
- [x] 3.3 Add `/agents` page + SideNav link: load catalog, show roles + knobs (Astryx); verify page renders catalog from API
- [x] 3.4 Update `frontend/AGENTS.md` for `/agents` and domain override; verify docs match UI

## 4. Integration

- [x] 4.1 Run `cd backend && .venv/bin/python -m pytest -q` and fix regressions
- [x] 4.2 Run frontend typecheck (`npx tsc --noEmit`) for touched app code
- [x] 4.3 Run `graphify update .` after code lands

## Workflow follow-up

- Archive after apply when ready
- `/commit-pr` when the user asks
