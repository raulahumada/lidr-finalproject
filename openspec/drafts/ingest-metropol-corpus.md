# Draft: ingest-metropol-corpus

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/ingestion/` (nuevo), `backend/app/generation/rag/` (chunking/embed reuse), `backend/app/foundation/persistence/` (store existente), `backend/app/config.py`, `backend/.env.example`, `AGENTS.md`, `backend/requirements.txt`
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/` @ `d2f015f` — `app/ingestion/` (loaders, `parsers/registry.py`, orchestrator)
- Patterns borrowed (not copied):
  - **ParserRegistry**: un parser por formato; formatos no registrados → skip (no crash)
  - Loader de filesystem que itera blobs bajo un root
  - Orquestador CLI/batch que: walk → parse → Document → (acá) chunk + embed + persist vía store existente
  - Corpus **fuera del repo** (`CORPUS_ROOT`); nunca commit de datos del cliente
  - Dominio Metropol Fintech (no presupuestos/JSON del estimador)

## Intent
Indexar el corpus real de Metropol Fintech (path local del usuario) en `documents`/`chunks` con embeddings, para que `POST /api/v1/search` recupere conocimiento de negocio en lugar del fixture de demo.

Alcance v1: allowlist **pdf / docx / txt / md** bajo `CORPUS_ROOT` (por defecto la carpeta Omnicanalidad/Agentes).

## Non-goals
- xlsx / xlsm / pptx / png / vsdx / mp4 / zip / sql / sh (skip + log; parsers después)
- OCR de imágenes o transcripción de video
- HTTP ingest API / UI / jobs en background con polling (CLI basta en v1)
- Pipeline PII completo del curso
- `/answer`, agentes, hybrid/HNSW
- Commitear archivos del corpus al git
- Reemplazar o borrar automáticamente todo el fixture (opcional: documentar convivencia o flag `--replace-fixture`)

## Draft requirements
- Setting `corpus_root` (`CORPUS_ROOT`) apuntando a un path absoluto local; documentado en `.env.example` (sin path personal hardcodeado en código).
- Allowlist configurable (default: `pdf,docx,txt,md`); extensiones fuera de lista → skip contado en el resumen del run.
- CLI documentado, p. ej. `python -m app.ingestion.run_ingest` (desde `backend/`), que:
  - Recorre `CORPUS_ROOT` recursivo
  - Parsea texto por formato (parsers registrados)
  - Trocea en chunks (estrategia simple: párrafos / fixed-size con overlap pequeño)
  - Embeddea con el mismo modelo que search (`text-embedding-3-small`)
  - Persiste vía `ChunkStore` / tablas existentes; **idempotente por `source_path`** (si ya existe, skip o replace documentado — propuesta: skip si mismo path ya ingerido, flag `--force` para re-ingerir)
- Resumen al final: files seen / ingested / skipped / failed + counts de chunks.
- Dependencias de parseo en `requirements.txt` (p. ej. `pypdf`, `python-docx`) con piso `>=`.
- Tests: parser de txt/md (y mocks para pdf/docx), skip de extensión desconocida, idempotencia básica sin llamar OpenAI (mock embedder).
- `AGENTS.md`: cómo setear `CORPUS_ROOT`, correr ingest, verificar con `/search`.
- Path de referencia del usuario (dev local, no en repo):  
  `/Users/rahumada/Documents/Corpus/Metropol Fintech - Omnicanalidad (Agentes)`  
  (o el parent `…/Corpus` si se prefiere; **propuesta: subcarpeta Metropol** para evitar ruido suelto en la raíz).

## Approach sketch
1. Añadir `app/ingestion/` al estilo curso **simplificado**:
   - `loaders/filesystem.py` — walk + filter por extensión
   - `parsers/protocol.py` + `txt.py` / `md.py` / `pdf.py` / `docx.py` + `registry.py`
   - `run_ingest.py` (CLI) u `orchestrator.py` + `__main__`
2. Chunking mínimo en `generation/rag/chunking.py` (o dentro de ingestion que llama a rag embed + foundation store) — respetar capas: ingestion puede usar `generation/rag` embedder + foundation store (como el curso: ingestion → rag).
3. Settings: `corpus_root`, `corpus_extensions` (string CSV).
4. No inventar segunda base; reutilizar Alembic/schema de `rag-chunks`.
5. Logs claros de skips (mp4/png/xlsx…).

## Practices check (backend | both only)
- Aligned:
  - Capas `ingestion` + `foundation/persistence` + `generation/rag`; routers sin lógica de ingest
  - Settings vía `get_settings()`; secretos/path por env
  - Reusar store/embedder existentes; no SQL en CLI crudo si hay repo
  - Deps en `requirements.txt` con `>=`
- Deviations (+ why):
  - Sin DataCatalog formal / jobs table del curso en v1. **Por qué:** un solo root local + CLI; catalog/jobs son overhead para el primer ingest Metropol.
  - Sin parsers xlsx aún (el curso tampoco los registra en el default S6). **Por qué:** priorizar docs narrativos pdf/docx.
- Risks if ignored:
  - Intentar indexar 2.9 GB (mp4/png) → costo/embeddings basura
  - Commitear corpus → riesgo de datos de cliente en git
  - Parsers en el router HTTP → mezcla de capas

## Impact
- backend: nuevo `app/ingestion/`, deps parseo, settings, CLI, tests, docs ops
- frontend: ninguno
- openspec: likely new capability `corpus-ingest` (o extensión de `rag-chunks` — **propuesta: capability nueva `corpus-ingest`** para no mezclar “store schema” con “batch ingest”)

## Open questions
- ¿Root = subcarpeta Metropol o todo `/Users/rahumada/Documents/Corpus`? **Propuesta: subcarpeta Metropol Fintech - Omnicanalidad (Agentes).**
- ¿Skip vs replace si `source_path` ya existe? **Propuesta: skip por defecto; `--force` re-ingiere (borra doc + chunks CASCADE y vuelve a cargar).**
- ¿Incluir xlsx en v1? **Propuesta: no** (siguiente change si hace falta FAQs tabulares).

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `ingest-metropol-corpus`
- Applied (ingest verified: 75 docs / 810 chunks)
- Synced to `openspec/specs/corpus-ingest/spec.md`
- Archived → `openspec/changes/archive/2026-10-08-ingest-metropol-corpus/`
- Logged in `openspec/history.md`
