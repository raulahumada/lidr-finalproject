# Draft: add-session-ownership

## Surface
- Primary: **backend**
- Secondary: **frontend** (docs / smoke only — BFF already sends `X-Console-User`; no UI redesign expected)
- Paths in this repo:
  - backend: `ConversationSessionRow` / Alembic; `SessionStore`; `answer_session.py` + agentic routes that touch `session_id`; optional thin dependency reading `X-Console-User`; tests
  - frontend: verify relay keeps header; `frontend/AGENTS.md` smoke note (no client changes if already same-origin BFF)
- Course reference: `session_16` / `ai-service` — no conversation-owner pattern found; layers: persist in foundation, thin routers, store in generation/conversation
- Peer Cristian (prior dual-auth notes): `X-Console-User` = Auth.js user id; absence → “sessions with no owner” (fail closed for cross-user leak)
- Patterns borrowed (not copied):
  - Trust header only from BFF+service token path (never invent owner in the browser)
  - 404 on foreign `session_id` (no “forbidden” oracle)
  - Nullable `owner_id` for pre-auth / script / eval sessions without header

## Intent
Cada operador de la consola debe ver y mutar **solo sus** conversaciones de chat. Hoy `list_summaries` / get / delete son globales: con dual-auth eso filtra personas en la puerta pero no el historial.

## Graphify notes
- Queried: conversation sessions SessionStore owner X-Console-User
- Hubs: `SessionStore` (`store.py`), `ConversationSessionRow`, `answer_session.py`, `answer_agentic.py`, frontend `sessions.ts` / `chat-sessions-context.tsx`, BFF `relay.ts` + `console-user.ts`
- Edges: UI → BFF (already sets `X-Console-User`) → FastAPI session CRUD / agentic with `session_id` → `SessionStore` (today unscoped)
- Gap: no `owner_id` column; store never reads console user; dual-auth archive explicitly deferred this follow-up
- Prefer extending `SessionStore` + Alembic on `conversation_sessions` over a parallel ownership table

## Non-goals
- Admin “ver todas las sesiones” / impersonation UI
- Multi-tenant orgs / teams
- Migrar ownership de filas legacy a un usuario concreto (quedan `owner_id` null)
- Cambiar Auth.js / roles / service token
- Ownership del LangGraph checkpointer (`thread_id` sigue independiente)

## Draft requirements

### A — Persist owner
- Alembic: columna `owner_id` nullable `String(64)` en `conversation_sessions` + índice (p. ej. `(owner_id, updated_at)` o `owner_id`)
- `SessionStore.create(owner_id=…)` escribe el valor (null permitido)

### B — Scope by `X-Console-User`
- Dependencia/helper en `api/` lee header `X-Console-User` (mismo nombre que el BFF); vacío / ausente → `owner_id=None` (modo script/legacy)
- Reglas:
  - **Con header:** list/get/rename/delete/append y uso agentic de `session_id` solo si `row.owner_id == header` (y filas con `owner_id` null **no** aparecen en la consola)
  - **Sin header:** list/get/… solo filas con `owner_id` IS NULL (eval/curl local); create deja null
- Acceso a sesión ajena → **404** (igual que desconocida)

### C — Wire all session touchpoints
- Routers `answer_session` (CRUD + list)
- Agentic start/sync/resume paths that `require` / `append_turn` with `session_id` — same ownership check before use
- Tests: create+list scoped; foreign get → 404; no-header vs with-header isolation

### D — Console smoke (no feature UI)
- Documentar en `frontend/AGENTS.md` / root: dos usuarios login → cada uno ve solo sus chats; BFF ya manda el header
- Front no cambia `lib/api/sessions.ts` si el relay ya adjunta el header

## Approach sketch
1. Migration + model field `owner_id`.
2. `SessionStore`: `create(owner_id)`, `list_summaries(owner_id=…)`, `get/require/rename/delete/append_turn` accept optional expected owner and enforce.
3. FastAPI Depends: `get_console_user_id(request) -> str | None` from `X-Console-User` (max 64 chars; drop over-long like BFF helper).
4. Pass into session routes + agentic `_require_session` / append paths.
5. Pytest focused on store + HTTP; keep empty-token open mode for API auth orthogonal to ownership.
6. Docs smoke; `graphify update .` after apply.

**OpenSpec capability (propuesta):** delta a `chat-sessions` (ownership) y/o new thin `session-ownership` — prefer **MODIFIED `chat-sessions`** + note in dual-auth follow-up closed.

## Practices check (backend | both only)
- Aligned: ownership enforcement at API/store boundary; Alembic for schema; routers stay thin; settings unchanged; header transport in `api/`
- Deviations: trusting `X-Console-User` only because service token already gates callers — **why:** BFF is the sole console caller with the secret; browser cannot forge successful FastAPI calls without the token in locked mode (open local mode: document that header spoofing is possible without token — same as today for all routes)
- Risks if ignored: list/get without filter → cross-user transcript leak; 403 vs 404 → user enumeration; creating without writing owner → sessions stay global forever

## Impact
- backend: Alembic, model, SessionStore, session + agentic routes, dependency, tests, AGENTS note
- frontend: docs/smoke only (header already sent)

## Open questions
- ¿Admin puede listar todas? → **Default: no** (v1).
- ¿Filas legacy `owner_id` null visibles en consola? → **Default: no** (solo sin header / scripts).
- ¿Nombre del change? → **Default: `add-session-ownership`**.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-session-ownership`
- [x] Applied, specs synced, archived
