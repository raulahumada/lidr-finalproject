# Tasks

## 1. Dependencies and settings

- [x] 1.1 Add `langgraph` to `backend/requirements.txt` and install in the venv; verify import `langgraph` succeeds
- [x] 1.2 Add agentic settings knobs if needed (e.g. confidence threshold) via `get_settings()` / `.env.example`; verify settings load without error

## 2. Graph core

- [x] 2.1 Add typed `AgenticAnswerState` (question, framed_query, hits, answer, citations, flags, review_reasons, agent_trace) under `domain/graph/`; verify type/import in a small unit test or compile check
- [x] 2.2 Implement specialists `intent_framer`, `corpus_fetcher` (only retriever caller), `grounded_composer` (reuse prompts v2 / blocks / ChatClient), `source_guard`; verify unit tests for no-evidence, citation filter, and that non-fetcher nodes do not call retrieve
- [x] 2.3 Implement `escalation_gate` with pure `review_reasons` and `interrupt()` only when non-empty; verify tests for fall-through vs pause triggers
- [x] 2.4 Wire `build.py` linear StateGraph + `MemorySaver` checkpointer in deps/lifespan; verify graph compiles

## 3. API and runner

- [x] 3.1 Implement `runner.py` (start + resume) and schemas for agentic request/response (status, thread_id, agent_trace, answer/citations)
- [x] 3.2 Add `POST /api/v1/answer/agentic` and resume route; mount on api router; verify 200 completed, 202 pause, 404 unknown thread, 503 missing key via API tests
- [x] 3.3 Document curl examples + MemorySaver caveat in `AGENTS.md`; verify commands match routes

## 4. Integration hygiene

- [x] 4.1 Run `cd backend && .venv/bin/python -m pytest -q` and fix regressions
- [x] 4.2 Run `graphify update .` from repo root so the knowledge graph includes `domain/graph`

## Workflow follow-up

- Archive the change after review; optional PR to `development` via commit-pr-development skill.
- Later: orchestrator hub + `AsyncPostgresSaver`; then S14-style LLM supervisor.
