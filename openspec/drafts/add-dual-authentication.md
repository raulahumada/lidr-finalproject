# Draft: add-dual-authentication

## Surface
- Primary: **both**
- Paths in this repo:
  - backend: `app/api/security.py` o middleware service-token; `config.py` (`SERVICE_TOKEN`, `APP_ENV`); tests; `AGENTS.md`
  - frontend: Auth.js (`auth.ts`, `/login`, `/register`), Prisma identity DB, `proxy`/middleware cookie gate, **BFF Route Handlers** que reenvían a FastAPI con Bearer; migrar `lib/api/*` de `NEXT_PUBLIC_API_BASE_URL` → same-origin `/api/...`; roles en layout/nav; Astryx login
- Course reference: `session_16` — `api/security.py` (X-API-Key por ruta) + `service_token.py` (middleware app-wide); **no** Auth.js (eso es peer)
- Peer Cristian (`.reference/lidr-master`):
  - Consola: Auth.js v5, Google + credentials, roles `usuario`/`administrador`, Prisma + `AUTH_DATABASE_URL`, cuentas nuevas deshabilitadas
  - Servicio: `SERVICE_TOKEN` + `Authorization: Bearer`, `/health` abierto; token solo en BFF `server-only`
- Patterns borrowed (not copied):
  - **Dos capas no intercambiables:** personas en la consola ≠ token del servicio
  - Token **nunca** en el browser (`NEXT_PUBLIC_` prohibido para el secreto)
  - Falla abierta en local sin token + warning; producción sin token → no arrancar (o 503 duro — ver defaults)
  - Sin inventar paquete monorepo compartido (`AGENTS.md`): BFF = Route Handlers dentro de `frontend/`

## Intent
Cerrar la API y la consola Metropol como Cris: (1) login de operadores con roles, (2) FastAPI solo acepta al BFF con token compartido — para que exponer `:8000` no deje ingest/settings/answer abiertos al mundo.

## Graphify notes
- Queried: CORS / `create_app` / `getApiBaseUrl` / fetch clients
- Hubs: `main.create_app` (solo CORS hoy), todos los clients `frontend/app/lib/api/*` pegan **directo** a `:8000`
- Gap: no hay middleware de auth, no hay `app/api` BFF en Next, no hay next-auth
- Constraint de diseño: con service token, **hay que dejar de llamar FastAPI desde el client component** salvo paths públicos inexistentes — el puente es BFF

## Non-goals
- Multi-tenant / org isolation
- Copiar catálogo VisualTIME / ownership headers avanzados del peer (`X-Console-User` ownership completo puede ser follow-up mínimo: opcional header user id)
- X-API-Key por router del curso (además del service token) — **v1 solo Bearer service token**
- SSO enterprise / SAML
- Sustituir Postgres del corpus; identity DB **aparte** (URL distinta)

## Draft requirements

### A — Service authentication (FastAPI)
- Setting `SERVICE_TOKEN` (vacío = modo abierto + log warning al boot si no es production)
- Middleware (o dependency global en `api_router`): exige `Authorization: Bearer <token>` comparado en tiempo constante
- Exentos: `GET {api_prefix}/health` (y opcionalmente `GET /` root + OpenAPI `/docs` en non-production — **propuesta: docs abiertos solo si token vacío o `APP_ENV!=production`**)
- `APP_ENV=production` + token vacío → **refuse to start** (como peer)
- Tests: 401 sin token cuando configurado; 200 health; happy path con header

### B — Console authentication (Next / Auth.js)
- Auth.js (NextAuth v5) en `frontend/`: Google + Credentials
- Roles: `usuario` | `administrador` en JWT/session
- Registro autoservicio → cuenta **disabled** hasta que admin habilita (pantalla `/users` admin o seed admin documentado)
- Identity store: Prisma + `AUTH_DATABASE_URL` (Postgres separado o DB distinta; **no** mezclar con tablas RAG)
- Gate: middleware/proxy — sin cookie → `/login`; layout console exige `auth()`
- Admin-only UI: `/settings`, `/ingest`, `/agents` (mutaciones), `/users`; `usuario` puede `/answer`, `/search`, home
- Login/register Astryx; smoke en `frontend/AGENTS.md`

### C — BFF bridge (obligatorio para que A+B cierren)
- Route Handlers under `frontend/app/api/**` relay a FastAPI con `SERVICE_TOKEN` server-side (`server-only` / no `NEXT_PUBLIC_SERVICE_TOKEN`)
- Refactor clients: base URL same-origin (`""` o `/api`) en vez de pegarle al puerto 8000 desde el browser
- BFF exige sesión Auth.js antes de relay (salvo `/api/auth/*`); admin routes del BFF chequean rol
- CORS: el browser habla al origin Next; FastAPI solo recibe tráfico server-to-server (localhost/docker) — documentar que `NEXT_PUBLIC_API_BASE_URL` deja de usarse para mutaciones (o solo para scripts)

## Approach sketch
1. **Backend first:** service-token middleware + settings + tests (curl local con header).
2. **Frontend Auth.js + Prisma** identity (seed admin).
3. **BFF relays** espejo de paths usados hoy (`answer`, `agentic`, `sessions`, `search`, `ingest`, `config/models`, `agents`).
4. **Point `lib/api/*` at BFF**; quitar secretos del client bundle.
5. **Role gates** en pages + BFF.
6. Docs: dos `.env` (backend `SERVICE_TOKEN`, frontend `AUTH_*` + `AI_SERVICE_URL` + `SERVICE_TOKEN` server-only).

**OpenSpec capabilities (propuesta):**
- `service-authentication` (delta/new)
- `console-authentication` (new)
- Opcional UI: requisitos de login dentro de `console-authentication`

Un solo change OpenSpec (grande) con tasks agrupadas Backend / Frontend-BFF / Frontend-Auth — evitar dos proposes desfasados que dejen un hueco (consola auth + API abierta).

## Practices check (backend | both only)
- Aligned: auth de transporte en `api/`; settings vía `get_settings()`; secretos en env; health sin auth pesada; routers de negocio sin lógica de login
- Deviations: BFF en Next (no paquete `business-backend` peer) — **por qué:** monorepo de dos apps, `AGENTS.md` prohíbe inventar carpeta compartida. Identity en Prisma (Node) no SQLAlchemy — **por qué:** Auth.js adapter; no mezclar users con RAG Alembic
- Risks if ignored: `NEXT_PUBLIC_SERVICE_TOKEN` → secreto filtrado; auth solo en UI sin token de servicio → bypass directo a `:8000`; token obligatorio sin BFF → rompe todos los clients de un golpe

## Impact
- backend: middleware service token, settings, boot guard, tests, docs
- frontend: Auth.js, Prisma, login/register/users, middleware, BFF routes, refactor `lib/api/*`, role-aware nav, docs
- ops: dos databases (corpus + auth), vars nuevas, Compose opcional segundo DB o misma instancia otra DB name

## Open questions
- ¿Google OAuth en v1 o solo credentials? → **Default: ambos** (como Cris); Google opcional si faltan client ids en local (documentar skip).
- ¿DB auth: segunda database en el mismo Postgres Compose (`entrega_lidr_auth`) o SQLite? → **Default: segunda DB en el Postgres Compose existente** (más cerca del peer, sin segundo contenedor).
- ¿Exponer `/docs` con token en prod? → **Default: no** (o Basic delante); local abierto si token vacío.
- ¿Header `X-Console-User` para ownership de sessions? → **Default: sí, mínimo** (pasar `session.user.id` en BFF) si no complica; si bloquea, defer a follow-up.
- ¿Un change o dos? → **Default: un change `add-dual-authentication`** con tasks A→C ordenadas.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-dual-authentication`
- [x] Applied, specs synced, archived
