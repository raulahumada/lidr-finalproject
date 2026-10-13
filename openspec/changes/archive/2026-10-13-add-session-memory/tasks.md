# Tasks

## 1. Conversation memory helpers

- [x] 1.1 Add settings `conversation_max_turns` (default 4) and `conversation_memory_max_tokens` (default 1024) to `config.py` + `.env.example`; verify `get_settings()` exposes both
- [x] 1.2 Implement `generation/conversation/resolver.py` (conservative Spanish referential resolve from window/last turn; expose `ResolvedQuestion` with `text` + `substituted`); verify unit tests: rewrite follow-up, leave self-contained unchanged, empty window no-op
- [x] 1.3 Implement `generation/conversation/budget.py` (`render_memory` + trim oldest turns under token ceiling); verify unit tests trim before exceeding budget and empty window returns no block

## 2. Graph + session wiring

- [x] 2.1 Extend `AgenticAnswerState` with `conversation_window`, `resolved_question` (and substituted list if needed); hydrate window from `SessionStore` in runner when `session_id` present; verify empty/missing session paths unchanged
- [x] 2.2 Upgrade `intent_framer` to call resolver and set `framed_query`/`resolved_question`; verify corpus_fetcher still consumes `framed_query` and agent_trace notes rewrite when substituted
- [x] 2.3 Inject budgeted memory block into `grounded_composer` / answer prompts (non-citable); verify citations still only from retrieved blocks and no-session prompts stay pass-through
- [x] 2.4 Persist optional `resolved_question` on `HistoryTurn` + `append_turn` when rewritten; verify session GET returns it and append-on-terminal tests still pass

## 3. Sync answer honesty + docs

- [x] 3.1 Reject `session_id` on `POST /answer` with HTTP 422 and a clear message pointing to agentic+session; verify TestClient case
- [x] 3.2 Update root `AGENTS.md` (memory ≠ transcript ≠ checkpointer; settings; sync 422); verify docs name the behavior

## 4. Integration check

- [x] 4.1 Run `cd backend && .venv/bin/python -m pytest -q` (resolver/budget + agentic/session + answer 422) and fix regressions
- [x] 4.2 Run `graphify update .` after code lands

## Workflow follow-up

- Archive after apply (`/opsx-archive`) when ready
- Commit/PR via `/commit-pr` when the user asks
