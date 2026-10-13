# Design

## Context

See proposal.md — Why. Today the browser calls FastAPI directly (`getApiBaseUrl` → `:8000`). `create_app` only adds CORS. Peer splits people auth (Auth.js + Prisma) from service auth (`SERVICE_TOKEN` + BFF). Course has middleware-style service token and optional per-route API keys; we take service token only for v1.

## Goals / Non-Goals

**Goals:**
- Close FastAPI to non-BFF callers when a token is configured
- Login + roles for the Next console
- Keep the service token off the JS bundle via same-origin BFF

**Non-Goals:**
- Second X-API-Key layer
- Multi-tenant
- Rewriting agentic/RAG domain logic

## Decisions

1. **One OpenSpec change, three implementation bands**  
   Backend token → Auth.js/Prisma → BFF + client migrate. Shipping console auth without BFF+token would leave `:8000` open.

2. **Service token middleware on the FastAPI app (or wrapping `api_router`)**  
   Constant-time compare of `Authorization: Bearer`. Exempt `GET {api_prefix}/health`. Root `/` and `/docs`/`/openapi.json` open only when token is empty or `app_env != production`.  
   *Alt:* Depends() on every router — easy to miss new routes; rejected.

3. **Boot policy**  
   Empty `SERVICE_TOKEN` + non-production → open + warning log. Empty + `app_env=production` → refuse to start.

4. **BFF = Next Route Handlers under `frontend/app/api/`**  
   Server reads `SERVICE_TOKEN` + `AI_SERVICE_URL` (no `NEXT_PUBLIC_`). Relays used surfaces: answer/agentic/sessions/search/ingest/config/models/agents. Requires Auth.js session; admin role for admin path groups.  
   *Alt:* separate `business-backend` package — forbidden by monorepo conventions.

5. **Clients use same-origin `/api/...`**  
   Change `getApiBaseUrl()` (or successor) to return `""` / relative `/api` for browser code. Scripts/curl still hit FastAPI with Bearer.

6. **Auth.js v5 + Prisma + second DB name**  
   `AUTH_DATABASE_URL` → e.g. `entrega_lidr_auth` on the same Compose Postgres. Roles `usuario`|`administrador`. New accounts disabled until admin enables. Seed documented admin. Google provider when env clients set; credentials always.  
   *Alt:* SQLite — weaker peer parity; rejected as default.

7. **Role matrix (UI + BFF)**  

   | Area | usuario | administrador |
   |------|---------|-----------------|
   | `/answer`, `/search`, home | yes | yes |
   | `/settings`, `/ingest`, `/agents`, `/users` | no | yes |

8. **`X-Console-User`**  
   BFF sets header to Auth.js user id for FastAPI to accept later ownership filters; v1 may only forward (store/filter can be stub or light session filter if already easy).

## Layer map

| Piece | Layer |
|-------|--------|
| `SERVICE_TOKEN` settings + boot check | config / main |
| Service token middleware | api (transport) |
| Auth.js + Prisma models | frontend identity (outside Python layers) |
| BFF route handlers | frontend transport |
| Domain answer/ingest routers | unchanged business logic |

**Tension:** identity is not in `foundation/persistence` Alembic — intentional isolation from RAG.

## Risks / Trade-offs

- [Large migrate of `lib/api/*`] → Mitigation: shared fetch helper first, then point base URL once
- [Local DX: token + two DBs] → Document Compose DB create + example tokens; empty token keeps current open mode
- [Google OAuth setup friction] → Credentials path works without Google env
- [Eval scripts hitting :8000] → Pass Bearer or run with empty SERVICE_TOKEN

## Migration Plan

1. Land backend token (default empty → no behavior change)
2. Land Auth.js + identity DB + login (pages gated; API still open if token empty)
3. Land BFF + switch clients + set tokens in `.env` for locked mode
4. Rollback: clear `SERVICE_TOKEN`, revert middleware; Auth.js can remain unused

## Open Questions

None (draft defaults locked).
