# Proposal: add-dual-authentication

## Why

The Metropol console and FastAPI are open on localhost: anyone who can reach `:8000` can ingest, change models, and spend OpenAI quota; the Next app has no login. Cristian closed this with two non-interchangeable layers (Auth.js for people + `SERVICE_TOKEN` for the AI service). We need the same shape before any non-local exposure, without inventing a third monorepo package.

## What Changes

- FastAPI: shared `SERVICE_TOKEN` via `Authorization: Bearer`; `/health` open; production refuse-to-start if token unset; local empty token remains open with a boot warning
- Next.js: Auth.js (Google + credentials), roles `usuario`/`administrador`, Prisma identity DB (`AUTH_DATABASE_URL`), register-disabled-until-admin, login/register/users UI
- BFF Route Handlers in `frontend/app/api/**` attach the service token server-side; browser `lib/api/*` calls same-origin BFF instead of `:8000`
- Role gates: admin for settings/ingest/agents/users; usuario for answer/search
- Minimal `X-Console-User` from BFF when session exists (session ownership follow-up stays thin)
- No **BREAKING** removal of existing path shapes behind the BFF (URLs change client-side only)

## Non-goals

- Multi-tenant orgs / SAML
- Course-style per-router X-API-Key in addition to service token
- Embedding service-token in `NEXT_PUBLIC_*`
- Full peer conversation-ownership suite beyond the user header

## Capabilities

### New Capabilities

- `service-authentication`: FastAPI bearer service token gate and boot policy
- `console-authentication`: Auth.js console login/roles/identity DB, BFF relay with token, and role-aware UI access

### Modified Capabilities

None at requirement level for RAG/answer contracts (transport and who may call change; answer payloads stay the same).

## Impact

- **Surface:** both
- **Backend:** middleware/settings/boot guard/tests/`AGENTS.md`/`.env.example`
- **Frontend:** Auth.js, Prisma, middleware, BFF routes, `lib/api/*` base URL, login/register/users, nav gates, docs
- **Ops:** second Postgres database name for identity; `SERVICE_TOKEN` on API + Next server; `AI_SERVICE_URL` server-only
- **Course/peer:** service-token middleware shape (course/peer); Auth.js + BFF pattern (peer), BFF hosted inside `frontend/`

### Graphify notes

- Hubs: `create_app` (CORS only today), `getApiBaseUrl` + all `lib/api/*` direct-to-8000 fetches
- This change inserts auth middleware on the API and a BFF hop so those clients no longer hold service secrets

## Practices check

- **Aligned:** transport auth in `api/`; secrets via env/`get_settings()`; thin routers; health stays light
- **Deviations:** BFF inside Next (not a `business-backend` package) — two-app monorepo rule; Prisma for identity (not SQLAlchemy) — Auth.js adapter, keep RAG Alembic clean
- **Risks if ignored:** public `SERVICE_TOKEN`; console-only auth with open `:8000`; enabling token without BFF breaks the UI
