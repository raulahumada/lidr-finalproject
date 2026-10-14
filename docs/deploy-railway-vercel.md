# Despliegue greenfield — Railway (API) + Vercel (consola)

Espejo operativo del peer lidr-master: **no hay job de CI que despliegue**; cada plataforma despliega desde GitHub.  
**No se entrena un modelo:** migrás esquema + ingerís embeddings desde tu Mac.

## Arquitectura de prod

| Recurso | Dónde | Para qué |
|---------|-------|----------|
| FastAPI | Railway service (`backend/`, Dockerfile) | search / answer / agentic / ingest HTTP |
| Postgres + pgvector | Railway | `documents`, `chunks`, sessions, agents, LangGraph checkpointer |
| Redis Stack | Railway | Response CAG |
| Postgres auth | Railway (segunda DB o servicio) | Prisma / Auth.js |
| Next.js | Vercel (`frontend/`) | consola + BFF |

```text
Browser → Vercel (Auth.js) → BFF → Railway API (Bearer + X-Console-User)
                ↓                         ↓
           Auth Postgres            RAG Postgres + Redis
```

## 0. Prerrequisitos

- Repo en GitHub (rama que Vercel/Railway van a trackear, p. ej. `development` o `main`)
- Cuenta Railway + Vercel
- CLI Railway instalada (el MCP de Cursor usa `railway mcp` — sin binario falla el discovery):

```bash
# macOS
brew install railway
# o: npm i -g @railway/cli
railway login
railway whoami
```

Reiniciá el MCP Railway en Cursor después del login.

- Token compartido:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Guardalo: mismo valor en Railway `SERVICE_TOKEN` y Vercel `SERVICE_TOKEN`.

## 1. Railway — bases y Redis

1. Crear proyecto vacío (dashboard o `railway init`).
2. Añadir **Postgres**. Anotá la URL pública (`DATABASE_URL`).
3. Conectar y habilitar pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE DATABASE entrega_lidr_auth;   -- identidad; nombre a elección
```

4. Añadir **Redis**. Preferí imagen compatible con RediSearch (Redis Stack) si el plugin default es alpine sin módulos — el Response CAG lo necesita. Anotá `REDIS_URL`.
5. Anotá la URL de la DB auth (mismo host, database `entrega_lidr_auth`, user/password del plugin).

## 2. Railway — servicio API

1. New service → Deploy from GitHub → root directory **`backend`**, builder **Dockerfile**.
2. Watch Paths: `backend/**` (evitar redeploy por cambios solo de front).
3. Healthcheck path: `/api/v1/health` (único endpoint abierto con token).
4. Variables (mínimo):

| Variable | Valor |
|----------|--------|
| `APP_ENV` | `production` |
| `DEBUG` | `false` |
| `SERVICE_TOKEN` | el generado arriba |
| `DATABASE_URL` | `postgresql+psycopg://…` (RAG; driver psycopg) |
| `REDIS_URL` | URL Redis |
| `OPENAI_API_KEY` | … |
| `CORS_ORIGINS` | `https://<tu-app>.vercel.app` (actualizar tras Vercel) |
| `AGENTIC_CHECKPOINTER` | `auto` |

Opcional: mismos knobs que `.env.example` (`ANSWER_PROMPT_VERSION`, umbrales, etc.).

5. Deploy. El `CMD` del Dockerfile corre `alembic upgrade head && uvicorn …`. Si la migración falla, el contenedor **no** se promueve.

Smoke:

```bash
curl -s https://<railway-api>/api/v1/health
# Con token el resto:
curl -s https://<railway-api>/api/v1/search \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"query":"ping","k":1}'
```

Corpus aún vacío → `results: []` es correcto.

## 3. Vercel — consola

1. Importar el repo → **Root Directory** = `frontend`.
2. Framework preset Next.js. Build: `npm run build` (ya incluye `prisma generate`).
3. Ignored Build Step (recomendado): salir 0 si el commit no toca `frontend/**`.
4. Variables de entorno (Production):

| Variable | Valor |
|----------|--------|
| `AUTH_SECRET` | `openssl rand -base64 32` |
| `AUTH_TRUST_HOST` | `true` |
| `AUTH_URL` | `https://<tu-app>.vercel.app` |
| `AUTH_DATABASE_URL` | Postgres auth (Railway) |
| `AI_SERVICE_URL` | `https://<railway-api>` (sin slash final) |
| `SERVICE_TOKEN` | **el mismo** que Railway |

5. Deploy.

**Orden recomendado (peer):** dejar Vercel arriba primero; después asegurar Railway con `SERVICE_TOKEN` + `CORS_ORIGINS`. Un header Bearer hacia un API todavía abierto se ignora; al revés la consola queda en 401.

## 4. Migraciones auth + primer admin (desde tu Mac)

No van en el build de Vercel (una DB un segundo caída no debe tumbar el deploy):

```bash
cd frontend
# AUTH_DATABASE_URL=… apuntando a Railway auth DB
npm run db:migrate
AUTH_SEED_PASSWORD='elegí-una' npm run seed:admin -- admin@tudominio.com
```

Login en la URL Vercel → `/users` para habilitar registros posteriores.

## 5. Ingest corpus desde tu máquina

Los archivos del cliente **no** se suben a Railway. Solo viajan embeddings:

```bash
cd backend
source .venv/bin/activate

# Temporal en shell o .env local (no commitear):
export DATABASE_URL='postgresql+psycopg://…'   # RAG de Railway (público)
export OPENAI_API_KEY='…'
export CORPUS_ROOT='/ruta/local/Metropol Fintech - Omnicanalidad (Agentes)'

# El contenedor ya migró; esto es no-op si head está aplicado:
alembic upgrade head
python -m app.ingestion.run_ingest
```

Smoke contra prod:

```bash
curl -s https://<railway-api>/api/v1/search \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"query":"cobranzas handoff Tenela","k":5}' | python3 -m json.tool
```

## 6. Checklist post-deploy

- [ ] `GET /api/v1/health` → 200
- [ ] Search con Bearer → hits del corpus
- [ ] Login consola + seed admin
- [ ] `/answer` crea sesión propia; otro usuario no la ve
- [ ] Agentic responde con citas (o pausa el gate de forma recuperable)
- [ ] `CORS_ORIGINS` incluye solo el origen Vercel
- [ ] Ningún secreto con prefijo `NEXT_PUBLIC_`

## Troubleshooting

| Síntoma | Causa probable |
|---------|----------------|
| MCP Railway “tool discovery failed” | CLI `railway` ausente o sin login |
| API no arranca en prod | `APP_ENV=production` sin `SERVICE_TOKEN` |
| Consola 401 en todas las llamadas | Token Vercel ≠ Railway, o Railway ya exige token y Vercel aún no lo tiene |
| Search vacío tras ingest | `DATABASE_URL` del CLI ≠ la del servicio API |
| Auth login falla | `db:migrate` no corrido / `AUTH_URL` ≠ URL Vercel |
| CAG no cachea | Redis sin RediSearch (imagen alpine) |

## Referencias

- [`backend/Dockerfile`](../backend/Dockerfile)
- [`backend/.env.example`](../backend/.env.example)
- [`frontend/.env.example`](../frontend/.env.example)
- [`docs/local-setup.md`](local-setup.md)
