# Proposal

## Why

Postgres + pgvector ya está levantado (`local-pgvector`), pero el backend aún no persiste chunks ni expone recuperación semántica. Sin Alembic, modelos y un `POST /search`, no se puede demostrar el primer slice RAG ni preparar la ingesta del corpus Metropol Fintech.

## What Changes

- Inicializar **Alembic** en `backend/` con migración que asegura la extensión `vector` y crea tablas `documents` / `chunks` (embedding `Vector(1536)` nullable).
- Introducir capas mínimas al estilo del curso dentro de `backend/app/`: `foundation/persistence/` + `generation/rag/` + router fino de search.
- Añadir dependencias Python: SQLAlchemy, Alembic, `psycopg[binary]`, `pgvector`, cliente OpenAI embeddings.
- Extender settings con `OPENAI_API_KEY` y modelo/dimensión de embedding (sin hardcodear secretos).
- Exponer `POST /api/v1/search` (query + k; corpus vacío → 200 con 0 results; sin API key → 503).
- Script CLI mínimo para seed de un documento fixture (probar punta a punta sin corpus del cliente).
- Documentar migraciones, env y curl de search en `AGENTS.md` / `.env.example`.
- Tests mínimos del endpoint (happy path / empty + validación de `k`).

## Non-goals

- `/answer`, multiagente, LangGraph, human gate
- UI / frontend
- Hybrid search, FTS, índices HNSW/IVFFlat
- Pipeline batch completo de `ingestion/` del curso
- Migrar CRUD `items` a Postgres
- Auth de servicio / deploy
- Indexar el corpus Metropol completo (queda para cuando exista path)

## Capabilities

### New Capabilities
- `rag-chunks`: Persistencia versionada de documentos y chunks con embeddings en pgvector (schema Alembic + capa foundation), más seed fixture local.
- `semantic-search`: Búsqueda semántica HTTP sobre chunks persistidos (`POST /api/v1/search`), con contrato tipado y degradación clara sin embeddings o con corpus vacío.

### Modified Capabilities
- (ninguna)

## Impact

- **Surface:** backend (+ docs ops en raíz).
- **Paths:** `backend/alembic*`, `backend/app/foundation/`, `backend/app/generation/rag/`, `backend/app/api/routes/search.py`, `backend/app/schemas/`, `backend/app/config.py`, `backend/app/dependencies.py`, `backend/requirements.txt`, `backend/.env.example`, tests bajo `backend/`, `AGENTS.md`.
- **APIs:** nuevo `POST /api/v1/search` (no breaking).
- **Deps:** nuevas en `requirements.txt` (SQLAlchemy, Alembic, psycopg, pgvector, openai).
- **Infra:** reutiliza Compose/`DATABASE_URL` de `local-pgvector`; no cambia el spec de esa capability.
- **Course ref:** forma S8 (`documents`/`chunks`, retriever, search fino) desde `session_16` / `.reference/ai-engineering/ai-service/`; dominio = Metropol, no estimador.

## Practices check

- **Aligned:**
  - Settings solo vía `get_settings()`; secretos por env
  - Routers finos; retrieval/SQL fuera de la ruta
  - Schemas Pydantic tipados + `response_model`
  - Prefijo `/api/v1`; router registrado en `api/router.py`
  - Capas `foundation` / `generation/rag` / `api` dentro de `backend/app/`
  - Persistencia con migraciones acordadas (Alembic), no SQL crudo en routers
- **Deviations:**
  - Path del curso `POST /search` sin versionar → nosotros `{api_prefix}/search`. Motivo: contrato actual del monorepo.
  - Seed fixture CLI en lugar de corpus Metropol. Motivo: path del cliente aún no disponible; no bloquea el slice.
  - Sin `ingestion/` batch ni conductor de dominio. Motivo: alcance = store + search; conductor llega con `/answer`.
- **Risks if ignored:**
  - SQL/embeddings en el router → deuda vs practices y referencia del curso
  - Sin Alembic → schema irreproducible entre máquinas
  - Meter hybrid/answer/UI en el mismo change → demora el primer demo verificable
