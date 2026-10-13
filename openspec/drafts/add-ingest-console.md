# Draft: add-ingest-console

## Surface
- Primary: **both**
- Paths in this repo:
  - backend: `app/api/routes/ingest.py` (nuevo), `app/schemas/ingest.py`, `app/api/router.py`, `app/dependencies.py`, reuso de `app/ingestion/orchestrator.run_ingest` + `run_ingest` CLI; opcional registry de jobs in-process
  - frontend: `app/ingest/page.tsx` (o similar), `app/lib/api/ingest.ts`, SideNav + home CTA opcional, `frontend/AGENTS.md`
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/` @ `d2f015f`
  - `app/api/ingestion.py` — `POST /runs` 202 + `BackgroundTasks`, `GET /jobs/{id}`
  - `app/api/routers/corpus_index.py` — index runs + poll + stats
  - `ARCHITECTURE.md` — routers finos; orchestrator fuera de `api/`
- Patterns borrowed (not copied):
  - Thin router: valida settings → crea job → dispatch background → 202 + id; **no** parsers en la ruta
  - Poll job status (mismo espíritu que agentic `/progress`)
  - Stats de corpus (docs/chunks) para la UI sin re-ingerir
  - Peer Cris: superficie tipo `/rag/index_runs` — nosotros: `/ingest` + API `/api/v1/ingest/*`
- Domain: Metropol Fintech / `CORPUS_ROOT` local (no catalog multi-source del estimador)

## Intent
Exponer la ingesta Metropol ya existente (`run_ingest`) por **HTTP + consola Astryx**, para que un operador pueda lanzar / forzar re-ingest y ver el resumen sin terminal — paridad demo con la consola de Cris, sin subir archivos ni inventar un segundo pipeline.

## Graphify notes
- Queried: `ingestion corpus run_ingest`, `run_ingest orchestrator iter_corpus_files`, path `run_ingest` → `api_router`
- Hubs / communities: `ingestion/orchestrator.py` (`run_ingest`, `IngestSummary`), `loaders.iter_corpus_files`, `ChunkStore`, `run_ingest.py` CLI, `routes/search.py` (consumidor del índice)
- Relevant paths / edges:
  - EXTRACTED: CLI → `run_ingest()` → parsers / chunk / embed / `ChunkStore`
  - **Gap confirmado:** `graphify path run_ingest api_router` → *No directed path* — hoy no hay puente HTTP
- Gaps: graph no conoce rutas frontend `/search` como consumidores de ingest (UI aparte); no bloquea el diseño

## Non-goals
- Upload de archivos desde el browser (sigue siendo path servidor `CORPUS_ROOT`)
- DataCatalog / include-exclude multi-source del curso
- Jobs durables en Postgres / Alembic en v1 (registry **in-process**, como activity log agentic; se pierde al reload de Uvicorn)
- Auth / API keys (siguiente change del lote)
- AI settings / model router (siguiente change)
- Parsers nuevos (xlsx, OCR, video)
- Cambiar chunking / embedding model desde esta pantalla
- Reemplazar o borrar el CLI (`python -m app.ingestion.run_ingest` sigue válido)

## Draft requirements
### Backend
- `POST /api/v1/ingest/runs` body opcional `{ "force": false }` → **202** + `{ run_id, status: "queued"|"running" }`
  - Usa `CORPUS_ROOT` + allowlist de settings; **sin** override arbitrario de root desde HTTP en v1 (evita path traversal / path remoto)
  - Si falta `CORPUS_ROOT` / embeddings / `DATABASE_URL` → **503** con detalle claro (misma semántica que CLI)
  - Dispara `run_ingest(...)` en `BackgroundTasks` (o thread equivalente al agentic start); actualiza job in-process
- `GET /api/v1/ingest/runs/{run_id}` → status `queued|running|completed|failed` + `IngestSummary` serializado cuando termine (seen / ingested / skipped_* / failed / chunks / errors truncados)
- `GET /api/v1/ingest/stats` → conteos actuales de documents/chunks (vía store/SQLAlchemy existente) + `corpus_root` configurado (path string) + allowlist — para pintar el estado del índice sin lanzar un run
- Router fino en `api/routes/ingest.py`; schemas en `schemas/ingest.py`; wiring en `dependencies` / composition root; **orquestador intacto**
- Tests: start → poll completed con embedder mock + corpus tmp; 503 sin CORPUS_ROOT; force flag llega al orchestrator (mock)
- Documentar curl en `AGENTS.md` junto al CLI

### Frontend
- Ruta `/ingest` en AppShell (SideNav, cerca de Búsqueda)
- Cliente tipado `lib/api/ingest.ts`: start + poll + stats
- UI Astryx: stats actuales → acción “Ingerir” / toggle force → poll mientras `running` → resumen + errores truncados → CTA a `/search`
- Workflow `astryx` (template + components); sin `<div>` ad-hoc
- Smoke en `frontend/AGENTS.md`; `tsc --noEmit`
- Home: CTA opcional “Corpus / Ingest” (nice-to-have; si no, solo SideNav)

## Approach sketch
1. **Backend — job registry in-process** (dict + lock, patrón `GraphActivityLog`): create → mark running → store summary/error → mark done. Un solo run concurrente: si ya hay `running`, **409** (v1 simple; evita doble embed del mismo corpus).
2. **Route** llama a `run_ingest` con los mismos deps que el CLI (`get_settings`, session factory, `OpenAIEmbedder`, `ChunkStore`).
3. **Stats**: método liviano en `ChunkStore` (o query count) — sin re-walk del filesystem.
4. **Frontend**: espejo de `/search` (client + page + nav); poll ~1–1.5s como agentic progress.
5. Extender capability OpenSpec `corpus-ingest` (delta) + capability UI `ingest-console` o un solo delta bajo `corpus-ingest` con requisitos UI — **propuesta: delta `corpus-ingest` (HTTP) + capability nueva `ingest-console-ui`** para separar contrato API de pantalla Astryx (como search).

## Practices check (backend | both only)
- Aligned:
  - Router fino; lógica en `ingestion/orchestrator` ya existente
  - Schemas Pydantic v2 Create/response; `response_model` + status 202/409/503/404
  - Settings vía `get_settings()`; secretos/path por env
  - Composition en dependencies; no SQL en router
  - Reuso de capas foundation + generation/rag embedder
- Deviations (+ why):
  - Jobs **in-process**, no `JobsRepository`/Alembic del curso. **Por qué:** un operador local + demo; durable jobs son el siguiente incremento si hace falta F5 mid-run.
  - Sin DataCatalog. **Por qué:** un solo `CORPUS_ROOT` Metropol ya configurado.
  - Sin override de `root` por HTTP. **Por qué:** superficie de ataque / paths arbitrarios; CLI conserva `--root`.
- Risks if ignored:
  - Lógica de parse en el router → mezcla de capas
  - Runs concurrentes → costo OpenAI duplicado / races en skip/force
  - Permitir `root` remoto sin auth → lectura de filesystem del host

## Impact
- backend: rutas ingest, schemas, job registry, stats en store, tests, AGENTS.md
- frontend: page `/ingest`, client API, SideNav (+ CTA home opcional), docs Astryx
- openspec: delta `corpus-ingest` + `ingest-console-ui` (o nombre final en propose)

## Open questions
- ¿Jobs durables (Alembic) en v1? → **Default: no** (in-process + 409 si busy).
- ¿Override de `CORPUS_ROOT` desde UI? → **Default: no** (solo settings/CLI).
- ¿CTA en home? → **Default: sí**, una línea junto a Búsqueda.
- ¿Bloquear segundo run con 409 o encolar? → **Default: 409**.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-ingest-console`
- Applied + synced to main specs + archived → `openspec/changes/archive/2026-10-13-add-ingest-console/`
- Logged in `openspec/history.md`
