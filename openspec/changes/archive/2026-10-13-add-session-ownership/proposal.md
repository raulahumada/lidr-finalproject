# Proposal

## Why

Dual authentication closes who can enter the console, but chat sessions remain single-tenant: any signed-in operator can list, open, and delete every conversation. With more than one user that is a transcript leak. The BFF already sends `X-Console-User`; FastAPI does not yet scope sessions by it.

## What Changes

- Persist optional `owner_id` on `conversation_sessions` (Auth.js user id from `X-Console-User`)
- Scope create/list/get/rename/delete and agentic use of `session_id` by that owner
- Foreign or mismatched sessions → HTTP 404 (same as unknown)
- No header → only unowned (`owner_id` null) rows (scripts/eval/legacy); console with header never sees others’ or null-owned rows
- Docs/smoke for two-user isolation; no Auth.js or service-token redesign

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities

- `chat-sessions`: list/read/mutate sessions are owner-scoped via `X-Console-User`; create stamps owner when the header is present

## Non-goals

- Admin “see all sessions” or impersonation
- Multi-tenant orgs/teams
- Reassigning legacy null-owned rows to a user
- Changing Auth.js, roles, or `SERVICE_TOKEN`
- Ownership of LangGraph checkpointer / `thread_id`

## Practices check

- **Aligned:** Alembic for schema; ownership enforced at API/store boundary; thin routers; header helper in `api/`; domain store stays in `generation/conversation`
- **Deviations:** Trust `X-Console-User` from the request — **why:** callers are already gated by `SERVICE_TOKEN` in locked mode; the BFF is the only console holder of both. Open local mode can spoof the header the same way it can call any route without a token today (documented).
- **Risks if ignored:** cross-user list/get; 403 vs 404 enumeration; create without writing owner leaves sessions global

## Impact

- **backend:** Alembic + `ConversationSessionRow`; `SessionStore`; `answer_session` + agentic session checks; Depends for console user; tests; AGENTS note
- **frontend:** docs/smoke only (BFF already attaches `X-Console-User`)
- **Graphify notes:** hubs `SessionStore`, `answer_session.py`, `answer_agentic.py`, BFF `relay.ts` / `console-user.ts` — extend store + routes, no parallel ownership island

## Surface

Primary **backend**; secondary frontend docs only.
