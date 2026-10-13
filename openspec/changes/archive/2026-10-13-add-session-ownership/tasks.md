# Tasks

## 1. Backend — schema + store

- [x] 1.1 Add nullable `owner_id` (String 64) + index on `conversation_sessions` via Alembic and `ConversationSessionRow`; verify `alembic upgrade head` applies cleanly
- [x] 1.2 Extend `SessionStore` create/list/get/require/rename/delete/append to stamp and enforce owner scope (header present vs null-only); verify unit/store tests for isolation and foreign → not found
- [x] 1.3 Add API helper/Depends reading `X-Console-User` (drop empty/over-long); verify unit or route test for parse rules

## 2. Backend — HTTP + agentic

- [x] 2.1 Wire `answer_session` create/list/get/patch/delete to pass console user into the store; verify HTTP tests: two owners isolated, foreign get → 404, no-header sees only unowned
- [x] 2.2 Apply the same ownership check on agentic paths that require or append with `session_id`; verify foreign `session_id` → 404 on start/sync/resume as applicable
- [x] 2.3 Document header behavior for scripts/eval in root `AGENTS.md` (unowned bucket); verify note exists

## 3. Frontend — docs only

- [x] 3.1 Confirm BFF still sends `X-Console-User` on session/agentic relays; add two-user smoke note to `frontend/AGENTS.md`; verify no client code change required (or minimal if a path skipped the relay)

## 4. Integration check

- [x] 4.1 Smoke: two console users → each SideNav conversations list is private; cross-open deep link → 404/empty
- [x] 4.2 Run focused pytest for session ownership + `graphify update .`

## Workflow follow-up

- Sync/archive after apply + commit-pr
