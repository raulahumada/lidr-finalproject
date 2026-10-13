# Proposal: add-answer-evaluation

## Why

The Metropol agentic path can produce long, plausible answers that over-claim when retrieval is thin. Without a runnable evaluation harness, quality is anecdotal. A small golden set + deterministic citation/abstention checks (course-style, not RAGAS yet) makes regressions measurable before demo day.

## What Changes

- Add `backend/eval/`: golden set JSON, pure scoring module, CLI harness calling sync `POST /answer/agentic`
- Optional `--auto-approve` resume when a case lands in human review so the draft can still be scored
- Write JSON reports under `backend/eval/reports/` (ignored except `.gitkeep`)
- Offline unit tests for the scorer; document how to run the live harness in root `AGENTS.md`
- **No** RAGAS, **no** CI gate on live LLM calls, **no** frontend

## Capabilities

### New Capabilities

- `answer-evaluation`: offline-scorable golden harness for Metropol agentic answers (citations, mentions, pause/no-evidence expectations)

### Modified Capabilities

None (consumes existing `agentic-answer` HTTP contract; does not change API requirements).

## Impact

- **Surface:** backend
- **Code:** `backend/eval/*`, `backend/tests/test_eval_scoring.py`, root `AGENTS.md`, `.gitignore`
- **API:** none (client of existing agentic endpoints)
- **Graphify hubs:** `AgenticAnswerRunner`, `source_guard`, `citations_valid` / `Citation` (consume via HTTP)
- **Practices check:**
  - Aligned: harness outside `app/api`; pure scorer; no secrets in fixtures
  - Deviations: `backend/eval/` sibling of `app/` (peer pattern) — eval is not a generation layer
  - Risks if ignored: flaky paid CI, or scoring stuck inside the runner
