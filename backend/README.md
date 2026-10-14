# Entrega LiDR — servicio API (backend)

Pipeline RAG + answer sync/agentic para el corpus **Metropol Fintech**.  
Uno de los dos proyectos del monorepo; el otro es `frontend/`. Portada: [README de la raíz](../README.md).

**Todos los comandos de este archivo corren desde `backend/`**, salvo Compose (raíz).

## Puesta en marcha

```bash
cd backend
cp .env.example .env          # DATABASE_URL, OPENAI_API_KEY, …
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
(cd .. && docker compose up -d)   # Postgres pgvector + Redis Stack
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000  docs: /docs
pytest -q
```

Sin `OPENAI_API_KEY`, search/answer responden **503**. Corpus vacío → search **200** con `results: []`.

### Variables que rompen si faltan

El detalle vive en [`.env.example`](.env.example). Resumen:

| Variable | Si falta / vacía |
|----------|------------------|
| `DATABASE_URL` | Alembic y retrieve fallan |
| `OPENAI_API_KEY` | search / answer / ingest → 503 o CLI abort |
| `REDIS_URL` | Response CAG soft-fail; answer sync sigue |
| `SERVICE_TOKEN` | Local: API abierta (warning). `APP_ENV=production` + vacío → **no arranca** |
| `CORPUS_ROOT` | Ingest CLI/HTTP no encuentra archivos |
| `CORS_ORIGINS` | Browser directo al API (la consola usa BFF; igual hay que listar el origen Vercel en prod) |

## Mapa de capas

```text
app/
├── main.py              # create_app(), CORS, SERVICE_TOKEN middleware, lifespan checkpointer
├── config.py            # Settings (Pydantic) desde .env
├── dependencies.py      # Composition root (retriever, stores, runners)
├── api/                 # Transporte HTTP fino
│   ├── service_token.py # Bearer app-wide (health abierto)
│   ├── console_user.py  # X-Console-User → ownership de sesiones
│   └── routes/          # health, search, answer, agentic, session, ingest, agents, …
├── domain/              # Orquestación de negocio (answer service, grafo LangGraph)
├── generation/          # RAG, CAG, conversation memory, prompts Jinja
├── ingestion/           # Walk CORPUS_ROOT → parse → chunk → embed → store
├── foundation/          # persistence SQLAlchemy, prompts, LLM helpers
└── schemas/             # Contratos Pydantic (request/response)
```

Specs normativas: `openspec/specs/` en la raíz del monorepo.

## Persistencia (pgvector)

```bash
(cd .. && docker compose up -d)
alembic upgrade head
```

Tablas principales: `documents`, `chunks` (embedding `Vector(1536)`), `conversation_sessions`, `agent_profiles`, más tablas LangGraph del checkpointer (creadas con `setup()` al boot, no Alembic).

Seed de fixture (sin corpus del cliente):

```bash
python -m app.generation.rag.seed_fixture   # requiere OPENAI_API_KEY
```

## Ingest del corpus Metropol

El corpus **no** está en el repo. Apuntá `CORPUS_ROOT` a la carpeta local. Allowlist: `CORPUS_EXTENSIONS` (default `pdf,docx,txt,md`).

```bash
python -m app.ingestion.run_ingest
python -m app.ingestion.run_ingest --force   # regenerar chunks/embeddings
```

También hay HTTP admin: `POST /api/v1/ingest/runs` (+ UI `/ingest` en la consola).

**Producción:** ingerí desde tu máquina contra el `DATABASE_URL` público de Railway (ver [`docs/deploy-railway-vercel.md`](../docs/deploy-railway-vercel.md)). No hace falta subir PDF al servidor: solo persisten chunks + vectors.

## Search / Answer / Agentic

```bash
curl -s http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"cobranzas handoff","k":5}' | python3 -m json.tool

curl -s http://localhost:8000/api/v1/answer \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Cómo es el handoff de cobranzas con Tenela?","k":5}' | python3 -m json.tool
```

Agentic (star + gate humano): ver raíz [`AGENTS.md`](../AGENTS.md) o:

```bash
curl -s http://localhost:8000/api/v1/answer/agentic \
  -H 'Content-Type: application/json' \
  -d '{"question":"¿Cómo es el handoff de cobranzas con Tenela?","k":5}'
```

Si `SERVICE_TOKEN` está seteado, todas las rutas excepto `/api/v1/health` exigen `Authorization: Bearer <token>`.

### LLM usage (ledger Postgres)

Cada `complete_json` exitoso en answer (sync / agentic) escribe una fila en `llm_usage_events`. Las respuestas llevan `usage` (última completion; ceros si no hubo llamada). Agregados:

```bash
curl -s 'http://localhost:8000/api/v1/usage/summary' | python3 -m json.tool
# filtros: from, to, session_id, purpose=answer|grounded_composer|prompt_specialist
```

### Sesiones y ownership

- `session_id` — transcript durable (Postgres); opcional en agentic.
- `thread_id` — pause/resume de un run LangGraph (checkpointer).
- Con header `X-Console-User`, list/get/patch/delete solo ven sesiones del owner; sin header (scripts) el comportamiento legacy aplica a sesiones sin owner.

## Docker (Railway)

[`Dockerfile`](Dockerfile): migra con Alembic y después sirve Uvicorn en `$PORT`. Healthcheck: `GET /api/v1/health`.

```bash
docker build -t entrega-lidr-api .
docker run --rm -p 8000:8000 --env-file .env -e PORT=8000 entrega-lidr-api
```

## Eval (no CI)

```bash
python -m eval.run_eval --limit 1 --auto-approve
python -m eval.run_multiturn --limit 1 --auto-approve
```

Reports en `eval/reports/` (gitignored). Scorer offline: `pytest -q tests/test_eval_scoring.py`.

## Tests

```bash
pytest -q
```

Los tests limpian `SERVICE_TOKEN` vía fixtures para no exigir bearer en el suite.
