# Entrega LiDR — guía para agentes

**Producto:** plataforma **multiagente + RAG** para el Máster AI Engineering (LIDR), con cliente **Metropol Fintech**. El corpus RAG es la documentación de omnicanalidad/agentes del cliente (también en NotebookLM).

Este archivo es la guía **operativa** del código para agentes. No duplicar ensayos de producto ni de deploy:

| Documento | Rol |
|-----------|-----|
| [`README.md`](README.md) | Producto, arquitectura, auth dual, deploy a alto nivel |
| [`backend/README.md`](backend/README.md) | API: capas, ingest, agentic, Docker |
| [`frontend/README.md`](frontend/README.md) | Consola: Auth.js, BFF, scripts |
| [`docs/local-setup.md`](docs/local-setup.md) | Paso a paso local |
| [`docs/deploy-railway-vercel.md`](docs/deploy-railway-vercel.md) | Greenfield Railway + Vercel + ingest remoto |
| [`frontend/AGENTS.md`](frontend/AGENTS.md) | Next canary + Astryx |
| `openspec/specs/` | Comportamiento normativo actual |
| `openspec/drafts/` | Borradores **locales** de `/opsx-prespec` (gitignored; no PR) |

## Estructura

```
entrega-lidr/
├── AGENTS.md            ← este archivo (contexto operativo)
├── README.md            ← producto + arquitectura
├── docs/                ← local-setup + deploy
├── docker-compose.yml   ← Postgres 16 + pgvector + Redis + pgAdmin
├── docker/              ← init SQL (extensión vector)
├── backend/             ← FastAPI (+ Dockerfile Railway)
└── frontend/            ← Next.js 16 + React 19 + Astryx
```
## Base de datos local (Postgres + pgvector + pgAdmin)

Credenciales en la **raíz**: copiá `.env.example` → `.env` y reemplazá los placeholders. Compose lee ese `.env` solo; no van passwords en `docker-compose.yml`.

```bash
cp .env.example .env   # editar POSTGRES_* y PGADMIN_*
docker compose up -d
docker compose ps   # postgres healthy
```

Verificar extensión `vector` (user/db = valores de tu `.env`):

```bash
# macOS / zsh o bash: cargá vars del .env de la raíz si hace falta
set -a && source .env && set +a
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Si preferís literales: `docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT …"` con los valores de tu `.env`.

Scripts de agentes (prespec, etc.) asumen **bash en macOS**; no dependen de PowerShell.

- **API / tools en el host:** `DATABASE_URL` en `backend/.env` (plantilla `backend/.env.example`); debe usar el mismo user/password/db que el Compose root `.env`.
- **pgAdmin:** http://localhost:5050 — login = `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD` de tu `.env`.
  - Al registrar el server: Host = `postgres` (nombre del servicio Compose), Port `5432`, DB/User/Password = `POSTGRES_*` del `.env`.
  - No uses `localhost` como host *desde dentro* de pgAdmin: ese hostname es el contenedor de pgAdmin, no Postgres.

```bash
docker compose down      # para contenedores; conserva volumen pgdata
docker compose down -v   # además borra datos
```

## Backend (`backend/`)

Stack: FastAPI, Uvicorn, Pydantic Settings, python-dotenv.

| Path | Rol |
|------|-----|
| `app/main.py` | Factory `create_app()`, CORS, monta router |
| `app/config.py` | Settings desde `.env` (`get_settings()` cacheado), incluye `database_url` + embeddings |
| `app/dependencies.py` | Composition root (retriever, etc.) |
| `app/api/router.py` | Agrega routers de rutas |
| `app/api/routes/health.py` | `GET /api/v1/health` |
| `app/api/routes/search.py` | `POST /api/v1/search` (semántico sobre chunks) |
| `app/api/routes/ingest.py` | `POST/GET /api/v1/ingest/*` (runs + stats; jobs in-process) |
| `app/api/routes/config_models.py` | `GET/PUT /api/v1/config/models` (runtime chat roles; Redis) |
| `app/foundation/persistence/` | SQLAlchemy engine, modelos `documents`/`chunks`, store |
| `app/generation/rag/` | Embedder OpenAI, retriever, seed fixture |
| `app/schemas/` | Contratos Pydantic (search, answer, session, …) |
| `alembic/` | Migraciones (pgvector chunks) |
| `.env.example` | Plantilla de env |

API prefix por defecto: `/api/v1`. Docs: `/docs`.

CORS por defecto: `http://localhost:3000`, `http://localhost:5173`.

**Python:** 3.10+ (recomendado 3.12 vía Homebrew). Crear venv: `cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

**RAG (chunks + search):** tablas `documents` / `chunks` vía Alembic; embeddings `text-embedding-3-small` (1536-d). Sin `OPENAI_API_KEY`, search responde **503**. Corpus vacío → **200** con `results: []`.

### Correr backend

```bash
cd backend
cp .env.example .env   # si hace falta; alinear DATABASE_URL con root Compose
# editar OPENAI_API_KEY=
source .venv/bin/activate   # o: python3.12 -m venv .venv && …
uvicorn app.main:app --reload
```

### Service token (BFF / scripts)

`SERVICE_TOKEN` en `backend/.env`: vacío en local → API abierta + warning al boot; con valor → hace falta `Authorization: Bearer <token>` en todo salvo `GET /api/v1/health`. `APP_ENV=production` sin token → el proceso **no arranca**. El front no debe usar `NEXT_PUBLIC_` para este secreto (lo pone el BFF de Next).

```bash
# con token configurado:
curl -s http://localhost:8000/api/v1/health
curl -s http://localhost:8000/api/v1/search \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"query":"cobranzas","k":3}'
```

Dependencias: `requirements.txt`.

### Migraciones + seed + search (macOS / bash)

Con Postgres Compose healthy:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.generation.rag.seed_fixture   # requiere OPENAI_API_KEY
```

### Ingest corpus Metropol (macOS / bash)

El corpus del cliente **no** vive en el repo. Apuntá `CORPUS_ROOT` en `backend/.env` a la carpeta local, p. ej.:

`/Users/…/Documents/Corpus/Metropol Fintech - Omnicanalidad (Agentes)`

Allowlist por defecto: `pdf,docx,txt,md` (`CORPUS_EXTENSIONS`). El resto se salta (xlsx, mp4, png, …).

Chunking: **recursive** (~512 tokens) para pdf/docx/txt; **headers Markdown** para `.md`. Parse sigue con `pypdf` / `python-docx`. Tras cambiar el chunker, re-ingerí con `--force` para regenerar embeddings.

```bash
cd backend
source .venv/bin/activate
# editar backend/.env → CORPUS_ROOT=…  OPENAI_API_KEY=…
python -m app.ingestion.run_ingest
# re-ingerir (p. ej. después de upgrade de chunking):
python -m app.ingestion.run_ingest --force
```

Misma ingesta por HTTP (consola `/ingest` o curl). Jobs **in-process** (se pierden al reload de Uvicorn; un run a la vez → 409):

```bash
# stats del índice
curl -s http://localhost:8000/api/v1/ingest/stats | python3 -m json.tool

# start (force opcional)
RUN=$(curl -s -X POST http://localhost:8000/api/v1/ingest/runs \
  -H 'Content-Type: application/json' \
  -d '{"force":false}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["run_id"])')

# poll hasta completed|failed
curl -s "http://localhost:8000/api/v1/ingest/runs/${RUN}" | python3 -m json.tool
```

Ejemplo de búsqueda:

```bash
curl -s http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"cobranzas handoff","k":5}' | python3 -m json.tool
```

### Answer (RAG + Knowledge CAG + Response CAG)

Compose debe incluir **Redis Stack** (`redis` en `docker-compose.yml`) además de Postgres. `REDIS_URL=redis://localhost:6379` en `backend/.env`.

Flujo: caché exacta → caché semántica (`SEMANTIC_CACHE_LOG_ONLY=true` por defecto) → retrieve → presupuesto de contexto → pack Metropol + Jinja (`ANSWER_PROMPT_VERSION=v2` por defecto) → LLM → citas validadas.

Al cambiar prompts o `ANSWER_PROMPT_VERSION`, las claves de caché exacta cambian con la versión; si iterás el mismo `v2` (p. ej. reglas de grounding / abstención en `system.j2`) y ves respuestas viejas: `docker compose exec redis redis-cli FLUSHDB`. Preferir iterar `v2` + flush antes de crear `v3`.

### Runtime chat models (`/config/models` + UI `/settings`)

Overrides en Redis (`lidr:runtime_models`) por rol: `chat` (sync `/answer`), `composer` (grounded), `prompt_specialist` (customs). Fallback: override del rol → override `chat` → `CHAT_MODEL` del `.env`. Allowlist: `AVAILABLE_CHAT_MODELS`. **Embedding no se puede cambiar por HTTP.** Write sin Redis → **503**. Cambiar modelo puede seguir sirviendo hits de Response CAG hasta TTL — si la demo se ve “vieja”: `FLUSHDB`.

```bash
curl -s http://localhost:8000/api/v1/config/models | python3 -m json.tool
curl -s -X PUT http://localhost:8000/api/v1/config/models \
  -H 'Content-Type: application/json' \
  -d '{"models":{"composer":"gpt-4o","prompt_specialist":null}}' | python3 -m json.tool
```

```bash
docker compose up -d redis
cd backend && source .venv/bin/activate
# OPENAI_API_KEY + REDIS_URL en backend/.env
curl -s http://localhost:8000/api/v1/answer \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Cómo es el handoff de cobranzas con Tenela?","k":5}' | python3 -m json.tool
```

### Answer agentic (LangGraph)

**Topología star (orquestador):** el hub `orchestrator` elige el siguiente especialista con una **escalera determinista** (`intent_framer` → `corpus_fetcher` → `grounded_composer` → `source_guard`) y vuelve al hub tras cada especialista; al cerrar el ladder va a `escalation_gate`. Reusa retrieve/prompts v2 del path sync; **sin** Response CAG en el hot path.

**Orquestador ≠ domain tag ≠ “agentes de negocio”:**
| Concepto | Qué es |
|----------|--------|
| Pipeline / nodos | Especialistas LangGraph (roles del grafo) |
| Orquestador | Hub que rutea entre esos nodos (`routing_history`, tope `AGENTIC_ORCHESTRATOR_MAX_STEPS`, default `10`) |
| Domain tag | Etiqueta Metropol `ventas\|cobranzas\|operacion\|tenela\|general` (auto-detect o override en el request); **no** es un agente aparte |

**Catálogo / studio (consola):** `GET /api/v1/answer/agents` → builtins (read-only; prompt Jinja del composer) + customs (Postgres) + ladder + knobs. CRUD de **customs** solo: `POST/PATCH/DELETE /api/v1/answer/agents` (builtins → 405/409). Prompt builtin = `foundation/prompts/answer/{ANSWER_PROMPT_VERSION}/system.j2`; prompt custom = columna DB. Customs enabled entran al ladder vía nodo `prompt_specialist` (después de `corpus_fetcher`). UI: `/agents`. Alembic: `agent_profiles`.

**Checkpointer:** por defecto **Postgres** (`AGENTIC_CHECKPOINTER=auto` + `DATABASE_URL`) — pause/resume sobrevive reinicios de Uvicorn (tablas LangGraph vía `setup()` al boot; no Alembic). `AGENTIC_CHECKPOINTER=memory` fuerza `MemorySaver` in-process (tests / offline).

Si confianza < `AGENTIC_CONFIDENCE_THRESHOLD` (default `0.55`), sin evidencia, o citas inválidas → **202** + `thread_id`; luego resume.

**Live progress (consola):** `POST /answer/agentic/start` agenda en background (HTTP 202 + `thread_id`) y `GET /answer/agentic/{thread_id}/progress` narra nodos (incluye hub) mientras `running`. El **activity log** sigue **in-process** (se pierde al reload; un thread pausado igual se puede `resume` si el checkpointer es Postgres). Body de start/sync acepta `domain` opcional (omit / `auto` = detección; valor inválido → **422**). Respuestas agentic (sync / progress / resume) incluyen `custom_notes: [{key, note}, …]` cuando corrió un especialista custom (`prompt_specialist`); lista vacía si no.

**Sesiones de chat (`session_id` ≠ `thread_id`):** una sesión agrupa muchos runs agentic; el transcript vive en Postgres (`conversation_sessions`, Alembic).

| Acción | Endpoint |
|--------|----------|
| Crear | `POST /api/v1/answer/session` → 201 + `session_id` |
| Listar | `GET /api/v1/answer/sessions` |
| Ver / history | `GET /api/v1/answer/session/{id}` |
| Renombrar | `PATCH /api/v1/answer/session/{id}` `{"title":…}` |
| Borrar | `DELETE /api/v1/answer/session/{id}` → 204 |

**Ownership:** el BFF manda `X-Console-User` (Auth.js user id). Con header → cada operador ve solo sus sesiones (`owner_id`). Sin header (curl/eval) → solo sesiones *sin dueño* (`owner_id` null); create deja null. Sesión ajena → **404**.

Pasá `session_id` opcional en `POST /answer/agentic` y `/answer/agentic/start`. Al terminar (`completed` / `rejected`, también tras resume) se appendea el turno al history. Sin `session_id`, el comportamiento anterior no cambia.

**Tres conceptos distintos:**

| Concepto | Qué es |
|----------|--------|
| Transcript / `session_id` | Historial durable en Postgres (UI + F5) |
| Checkpointer / `thread_id` | Estado pausado de **un** run LangGraph |
| Conversation memory | Con `session_id`: (1) ventana de turnos, (2) **facts** (dominio / entidades / docs citados, sin LLM extract), (3) **anchors** (frases de alcance ES → dominio). Un turno *solo-ancla* confirma y no hace RAG. Resolve + `render_memory` los usan; request `domain` gana sobre anchor. Settings: `CONVERSATION_MAX_TURNS` (default 4), `CONVERSATION_MEMORY_MAX_TOKENS` (default 1024). Bag en `conversation_sessions.memory` (JSONB) |

`POST /answer` (sync, un tiro) **rechaza** `session_id` con HTTP **422** — no tiene framing de memoria; usá agentic + session.

```bash
cd backend && source .venv/bin/activate
alembic upgrade head   # incluye conversation_sessions
# OPENAI_API_KEY en backend/.env
SESSION=$(curl -s -X POST http://localhost:8000/api/v1/answer/session | python3 -c 'import sys,json; print(json.load(sys.stdin)["session_id"])')

curl -s -w '\nHTTP %{http_code}\n' http://localhost:8000/api/v1/answer/agentic \
  -H 'Content-Type: application/json' \
  -d "{\"question\":\"¿Cómo es el handoff de cobranzas con Tenela?\",\"k\":5,\"session_id\":\"$SESSION\"}" | python3 -m json.tool

# Live progress (start + poll):
THREAD=$(curl -s -X POST http://localhost:8000/api/v1/answer/agentic/start \
  -H 'Content-Type: application/json' \
  -d "{\"question\":\"¿Cómo es el handoff de cobranzas con Tenela?\",\"session_id\":\"$SESSION\"}" | python3 -c 'import sys,json; print(json.load(sys.stdin)["thread_id"])')
curl -s "http://localhost:8000/api/v1/answer/agentic/${THREAD}/progress" | python3 -m json.tool

# Si status=awaiting_human_review (HTTP 202 sync, o progress terminal), retomá con el thread_id:
curl -s http://localhost:8000/api/v1/answer/agentic/<thread_id>/resume \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approve"}' | python3 -m json.tool
# decision: approve | reject | adjust (+ adjusted_answer opcional)
```

Tests: `cd backend && .venv/bin/python -m pytest -q`.

### Eval harness (agentic, no CI)

Golden set + scoring determinista (citas / mentions / pause / `no_evidence`). **No** RAGAS; **no** corre en pytest por defecto (gasta tokens).

Prerrequisitos: Postgres + Redis up, `OPENAI_API_KEY`, corpus ingerido, API en `:8000`.

```bash
cd backend && source .venv/bin/activate
# smoke un caso (1 turno):
python -m eval.run_eval --base-url http://localhost:8000 --limit 1
# caso concreto + auto-approve si pausa el gate humano:
python -m eval.run_eval --case cobranzas-handoff-tenela --auto-approve
# set completo → report en eval/reports/report-*.json (gitignored)
python -m eval.run_eval
```

Multiturn (misma sesión, mide rewrite / falso negativo del resolver):

```bash
python -m eval.run_multiturn --limit 1 --auto-approve
python -m eval.run_multiturn --case cobranzas-followup-tenela --auto-approve
# report: eval/reports/report-multiturn-*.json
```

Scorer offline: `pytest -q tests/test_eval_scoring.py`.

## Frontend (`frontend/`)

Stack: Next.js `16.3.5` (App Router), React `19.2.8`, TypeScript, Tailwind CSS 4, Astryx, Auth.js + Prisma.

Detalle: **`frontend/README.md`** + **`frontend/AGENTS.md`** (Astryx) antes de tocar UI.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run db:migrate && npm run seed:admin -- admin@example.com
npm run dev   # http://localhost:3000
```

Scripts: `dev`, `build`, `start`, `lint`, `db:migrate`, `db:generate`, `seed:admin`.

## Estado actual / gaps

- Sin package/workspace root; cada carpeta se instala y corre por separado.
- RAG + agentic + sessions + ownership + dual auth + ingest console cableados (ver README).
- Activity/progress agentic in-process (checkpointer Postgres sí sobrevive redeploy).
- Deploy: Railway (`backend/Dockerfile`) + Vercel (`frontend/`) — ver `docs/deploy-railway-vercel.md`.

## Convenciones para agentes

1. Cambios de API → `backend/`; UI → `frontend/`. No inventar carpetas compartidas sin pedirlo.
2. Antes de UI nueva: seguir el workflow de Astryx en `frontend/AGENTS.md` (`astryx build`, templates, components). No inventar layout con `<div>` + CSS a mano.
3. Next.js 16 puede diferir del entrenamiento: consultar docs bajo `frontend/node_modules/next/dist/docs/` cuando haga falta.
4. No commitear `.env` del backend; usar `.env.example` como referencia.
5. Preferir extender routers/schemas existentes (`search`, `answer`, `session`, …) antes de crear superficies paralelas, salvo que el usuario pida otra cosa.
6. Documentación de agente de producto vive aquí; reglas específicas de front viven en `frontend/AGENTS.md`.
7. Cambios alineados a la arquitectura del curso: `/opsx-prespec` (draft + sync referencia + surface front|back|both → OpenSpec propose). Implementar con `/opsx-apply`.
8. Backend Python: seguir y contrastar `docs/python-best-practices.md` en `/opsx-propose` y `/opsx-prespec` (sección Practices check).
9. **Graphify** (grafo local en `graphify-out/`): en `/opsx-prespec` y `/opsx-propose`, si existe `graphify-out/graph.json`, usar `graphify query` / `path` / `explain` antes de Grep/Glob amplios; registrar notas en el draft. Tras cambios de código: `graphify update .`.
10. **Drafts** (`openspec/drafts/`): solo locales; están en `.gitignore`. No incluir drafts en commits/PR. El change formal vive en `openspec/changes/` tras approve + propose.
