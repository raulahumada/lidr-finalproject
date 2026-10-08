# Draft: add-rag-chunks-and-search

## Surface
- Primary: **backend**
- Paths in this repo: `backend/` (Alembic, `app/foundation/persistence/`, `app/generation/rag/`, `app/api/routes/`, `app/schemas/`, `requirements.txt`, `.env.example`), `AGENTS.md` (cómo migrar / search)
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/` (synced @ `d2f015f`)
- Patterns borrowed (not copied):
  - Capas: `foundation/persistence` (engine/repos) + `generation/rag` (store/retriever) + router fino en `api`
  - Migración Alembic con `CREATE EXTENSION IF NOT EXISTS vector` + tablas `documents` / `chunks` + columna `embedding Vector(1536)` nullable
  - `POST /search` delgado: validación en schema, ranking en retriever; corpus vacío → **200 con 0 results** (no error)
  - Sin índice HNSW todavía (baseline seq scan como en S8 del curso)
  - Dominio/estimador del curso **no** se copia; corpus = Metropol Fintech cuando exista path

## Intent
Abrir el primer slice RAG usable: **migraciones + persistencia de chunks en pgvector + `POST /api/v1/search`**, sin agentes ni generación de respuesta.

Permite verificar el stack DB→embedding→rank con corpus vacío o con un seed mínimo; la ingesta masiva del corpus Metropol queda para cuando haya path de archivos.

## Non-goals
- `/answer`, orquestador multiagente, LangGraph, human gate
- UI / frontend / Astryx
- Hybrid search, FTS/`tsvector`, HNSW/IVFFlat
- Pipeline batch completo de `ingestion/` del curso (PII, catalog, parsers multi-formato)
- Migrar el CRUD `items` a Postgres
- Deploy (Railway/Vercel), auth de servicio
- Indexar el corpus Metropol completo (solo path/seed opcional cuando el usuario lo pase)

## Draft requirements
- Inicializar **Alembic** bajo `backend/` (`alembic.ini`, `alembic/env.py` leyendo `DATABASE_URL` vía settings).
- Primera migración (o equivalente inicial) que:
  - Asegure `CREATE EXTENSION IF NOT EXISTS vector`
  - Cree tabla `documents` (id, source_path, document_type, ingested_at, metadata JSONB)
  - Cree tabla `chunks` (id, document_id FK CASCADE, chunk_type, content, embedding Vector(1536) nullable, metadata JSONB, created_at)
  - Índices relacionales básicos (FK / source_path); **sin** índice vectorial aún
- Introducir layout de capas mínimo alineado al curso **dentro de** `backend/app/`:
  - `foundation/persistence/` — engine SQLAlchemy, session factory, modelos ORM / repos de chunks
  - `generation/rag/` — retriever semántico (embed query → cosine distance → top-k)
  - Router fino `api/routes/search.py` registrado en `api/router.py`
- Dependencias en `requirements.txt`: SQLAlchemy, Alembic, `psycopg[binary]`, `pgvector`, y cliente de embeddings (p. ej. `openai`) con piso de versión.
- Settings: reutilizar `database_url`; añadir settings necesarios para embeddings (p. ej. `openai_api_key`, modelo `text-embedding-3-small` / dim 1536) sin hardcodear secretos.
- Contrato HTTP: `POST {api_prefix}/search` con body `{ "query": str, "k": int }` (k con bounds razonables, default 5) y response tipada (query, k, results[], search_time_ms opcional).
  - Sin API key de embeddings configurada → **503** claro
  - Corpus vacío → **200** con `results: []`
- Documentar en `AGENTS.md`: `alembic upgrade head`, variables nuevas en `.env.example`, ejemplo de curl a `/search`.
- Seed/ingesta mínima (elige una en design/apply, no ambas a lo grande):
  - **Opción A (preferida):** script o endpoint interno mínimo que inserte 1 documento + N chunks de texto fixture (sin depender del corpus del cliente), para poder probar search de punta a punta con API key
  - **Opción B:** dejar search + schema listos; ingesta real en el siguiente change cuando exista path Metropol
- Tests mínimos: happy path search (mock retriever o empty corpus) + validación 422 de `k` fuera de rango (estilo curso `test_search_endpoint`).

## Approach sketch
1. Añadir deps + Alembic apuntando al Postgres Compose ya existente (`local-pgvector`).
2. Migración `documents`/`chunks` (forma S8 del curso; nombres de dominio genéricos, no “budget_*”).
3. `foundation/persistence`: engine desde `get_settings().database_url`, session dependency, modelos.
4. `generation/rag`: embedder + `SemanticRetriever` (cosine via pgvector/`<=>` o equivalente SQLAlchemy).
5. `POST /api/v1/search` en router nuevo; composition root liviano (`dependencies.py` si hace falta) — routers sin SQL/LLM inline.
6. Seed fixture opcional para demo local; corpus Metropol = follow-up con path del usuario.
7. Docs ops en `AGENTS.md` + `.env.example`.

Alineación a capas: esto es **foundation/persistence + generation/rag + api**; no hay conductor de dominio todavía (aparece con `/answer` / agentes).

## Practices check (backend | both only)
- Aligned:
  - Settings solo vía `get_settings()`; secretos por env
  - Routers finos; lógica de retrieval fuera de la ruta
  - Schemas Pydantic Create/request/response tipados + `response_model`
  - Prefijo `/api/v1` existente; nuevo router registrado en `api/router.py`
  - Capas al estilo curso **dentro de** `backend/app/`, sin renombrar el monorepo a `ai-service`
  - Sustituir patrón “SQL en router” / store en memoria para este feature
- Deviations (+ why):
  - Path del curso `POST /search` sin prefijo versionado → nosotros bajo `{api_prefix}/search` (**por qué:** contrato actual del monorepo)
  - Sin `ingestion/` batch del estimador ni dominio de presupuestos (**por qué:** dominio Metropol; alcance = persistencia + search)
  - Seed fixture en lugar de corpus cliente (**por qué:** el path del corpus aún no está; no bloquea el slice)
- Risks if ignored:
  - SQL/embeddings en el router → deuda vs practices + curso
  - Sin Alembic → schema irreproducible entre máquinas
  - Meter HNSW/hybrid/answer en el mismo change → scope creep y demora el primer demo verificable

## Impact
- backend: Alembic, deps, `foundation/persistence`, `generation/rag`, route `search`, schemas, settings, tests, `.env.example`
- docs: `AGENTS.md`
- frontend: ninguno

## Open questions
- ¿Incluir seed fixture (Opción A) en este change o dejar solo schema+search vacío (Opción B)? **Propuesta: Opción A** (1 doc fixture) para poder demostrar search sin esperar el corpus Metropol.
- ¿Cliente de embeddings solo OpenAI (`text-embedding-3-small`) en este slice? **Propuesta: sí** (igual que el curso S8); multi-proveedor después.
- ¿Endpoint de ingest HTTP ahora o solo script CLI? **Propuesta: script CLI mínimo** (`python -m …`) para no abrir superficie HTTP de escritura aún; HTTP ingest en un change siguiente si hace falta consola.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-rag-chunks-and-search`
- Synced to `openspec/specs/rag-chunks/spec.md` + `openspec/specs/semantic-search/spec.md`
- Archived → `openspec/changes/archive/2026-10-08-add-rag-chunks-and-search/`
- Logged in `openspec/history.md`
