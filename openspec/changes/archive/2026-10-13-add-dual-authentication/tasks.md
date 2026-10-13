# Tasks

## 1. Backend — service authentication

- [x] 1.1 Add `service_token` (+ document `APP_ENV` production behavior) to Settings and `backend/.env.example`; verify empty default keeps local open mode
- [x] 1.2 Implement bearer gate middleware/dependency (constant-time compare, health exempt, docs policy per design); wire in `create_app`; verify pytest 401/200-health/open-mode
- [x] 1.3 Implement production refuse-to-start when token empty; verify with a focused test or documented startup assertion
- [x] 1.4 Document curl-with-Bearer and open-mode warning in root `AGENTS.md`

## 2. Frontend — Auth.js + identity

- [x] 2.1 Add Auth.js v5 + Prisma identity schema and `AUTH_DATABASE_URL` (second DB on Compose Postgres); document create-DB + migrate + seed admin in `frontend/AGENTS.md`
- [x] 2.2 Implement login/register (credentials + Google when env set), disabled-until-admin rule, and `/users` admin enable/disable; verify smoke paths documented
- [x] 2.3 Add middleware/proxy + layout session gate (unauthenticated → login); verify protected routes redirect
- [x] 2.4 Enforce role matrix in UI (usuario vs administrador pages); verify forbidden/redirect for usuario on `/settings` and `/ingest`

## 3. Frontend — BFF + client migration

- [x] 3.1 Add server-only FastAPI relay helper (`AI_SERVICE_URL` + `SERVICE_TOKEN`, optional `X-Console-User`); verify token never under `NEXT_PUBLIC_`
- [x] 3.2 Implement BFF Route Handlers for answer/agentic/sessions/search/ingest/config/models/agents with session + role checks; verify anonymous → auth error
- [x] 3.3 Point `lib/api/*` at same-origin BFF base; verify `tsc --noEmit` and UI flows still typecheck
- [x] 3.4 Update `frontend/.env.example` + `frontend/AGENTS.md` (locked vs open local modes)

## 4. Integration check

- [x] 4.1 Smoke locked mode: tokens set → browser UI via login → admin ingest/settings work; curl to `:8000` without Bearer → 401; health → 200
- [x] 4.2 Smoke open mode: empty `SERVICE_TOKEN` → existing pytest suite still runnable; document any required test header helpers
- [x] 4.3 Run `graphify update .` after code lands

## Workflow follow-up

- Sync/archive after apply + commit-pr
- Optional later: stricter session ownership using `X-Console-User`
