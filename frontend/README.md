# Entrega LiDR — consola (frontend)

Consola Next.js para el RAG multiagente Metropol: login, chat agentic multi-sesión, search, ingest, catálogo de agentes, users/settings, **uso de tokens** admin.

Uno de los dos proyectos del monorepo; el otro es `backend/`. Portada: [README de la raíz](../README.md).

**Todos los comandos de este archivo corren desde `frontend/`.**

## Puesta en marcha

```bash
cd frontend
cp .env.example .env.local
npm install

# Auth DB (misma instancia Compose, otra database — ver docs/local-setup.md)
npm run db:migrate
npm run seed:admin -- admin@example.com   # o AUTH_SEED_PASSWORD=

npm run dev   # http://localhost:3000
```

UI kit: **Astryx** (`@astryxdesign/core` + theme). Antes de UI nueva: leer [`AGENTS.md`](AGENTS.md) (`npx astryx …`).

## Autenticación y BFF

| Pieza | Rol |
|-------|-----|
| Auth.js (`next-auth`) | Sesión de persona (credentials). Google diferido. |
| Prisma + `AUTH_DATABASE_URL` | Identidad (users, accounts, sessions) — **no** es la DB del corpus |
| BFF `app/api/v1/*` | Proxy same-origin → FastAPI con `SERVICE_TOKEN` + `X-Console-User` |
| Registro | Cuenta **disabled** hasta que un admin habilite en `/users` |

El browser **nunca** ve `AI_SERVICE_URL` ni `SERVICE_TOKEN` (sin `NEXT_PUBLIC_`). Toda mutación al API sale del servidor Next.

### Variables que rompen si faltan

Detalle en [`.env.example`](.env.example):

| Variable | Si falta |
|----------|----------|
| `AUTH_SECRET` | Auth.js no firma cookies |
| `AUTH_URL` | En Vercel, callbacks mal armados sin la URL pública |
| `AUTH_DATABASE_URL` | Login/registro fallan |
| `AI_SERVICE_URL` | BFF no alcanza Railway/local API |
| `SERVICE_TOKEN` | Debe coincidir con el backend; vacío solo en local abierto |

## Scripts

| Script | Qué hace |
|--------|----------|
| `npm run dev` | Next dev |
| `npm run build` | `prisma generate` + `next build` |
| `npm run db:migrate` | `prisma migrate deploy` (acto deliberado; **no** en el build de Vercel) |
| `npm run db:generate` | Solo client Prisma |
| `npm run seed:admin` | Primer admin (o `AUTH_SEED_PASSWORD`) |
| `npm run lint` | ESLint |

## Mapa de rutas (App Router)

```text
app/
├── (auth)/login|register     # credentials
├── (console)/
│   ├── answer/               # chat agentic multi-sesión
│   ├── search/
│   └── (admin)/
│       ├── agents/           # catálogo + customs
│       ├── ingest/
│       ├── users/
│       ├── settings/         # runtime chat models
│       └── usage/            # ledger tokens (admin)
├── api/auth/[...nextauth]    # Auth.js
└── api/v1/*                  # BFF → FastAPI (incl. /usage admin-only)
lib/auth/                     # roles, guards (`/usage`, `/api/v1/usage`)
lib/ai-service/               # relay Bearer + X-Console-User
app/lib/api/                  # clients tipados (answer, agentic, sessions, usage, …)
```

### Uso de tokens (`/usage`)

Solo `administrador` (SideNav **Sistema → Uso**). Lee `GET /api/v1/usage/summary` vía BFF: totales + por modelo; filtros fecha / purpose / `session_id`. Sin columna USD. Detalle del ledger: [`backend/README.md`](../backend/README.md) y [`AGENTS.md`](../AGENTS.md).

## Despliegue (Vercel)

Root directory: `frontend`. Guía: [`docs/deploy-railway-vercel.md`](../docs/deploy-railway-vercel.md).

Tras el primer deploy:

```bash
# contra AUTH_DATABASE_URL de prod
npm run db:migrate
AUTH_SEED_PASSWORD='…' npm run seed:admin -- admin@tudominio.com
```

`AI_SERVICE_URL` = URL pública del API en Railway (sin slash final).
