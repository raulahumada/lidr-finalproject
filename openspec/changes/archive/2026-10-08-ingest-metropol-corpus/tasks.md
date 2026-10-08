# Tasks

## 1. Settings and dependencies

- [x] 1.1 Add `corpus_root` and `corpus_extensions` (CSV, default `pdf,docx,txt,md`) to `Settings` + document in `backend/.env.example` — verify `get_settings()` loads defaults without requiring `CORPUS_ROOT`
- [x] 1.2 Add `pypdf` and `python-docx` to `backend/requirements.txt` with `>=` floors and install in venv — verify `import pypdf, docx` succeeds

## 2. Ingestion pipeline

- [x] 2.1 Implement filesystem walker + `ParserRegistry` with txt/md/pdf/docx parsers under `app/ingestion/` — verify unit tests: txt/md extract text; unknown extension not registered / skipped by walker
- [x] 2.2 Add simple chunker in `generation/rag` (paragraph / fixed-size fallback) — verify a long string yields >1 chunks with non-empty content
- [x] 2.3 Implement orchestrator: walk → parse → chunk → embed → `ChunkStore.persist`; skip existing `source_path`; `--force` deletes then re-ingests — verify with mock embedder against local DB (or transactional test)
- [x] 2.4 Add store helper to find/delete document by `source_path` if missing — verify delete cascades chunks

## 3. CLI and docs

- [x] 3.1 Ship `python -m app.ingestion.run_ingest` (or equivalent) printing seen/ingested/skipped/failed + chunk count; error if `CORPUS_ROOT` empty/missing — verify `--help` / missing root exits non-zero with clear message
- [x] 3.2 Update `AGENTS.md` with macOS steps: set `CORPUS_ROOT` to Metropol folder, run ingest, sample `/search` — verify commands match module path

## 4. Verification

- [x] 4.1 Run ingest against the developer Metropol corpus path (allowlisted only) with real `OPENAI_API_KEY` — verify summary shows ingested > 0 and skipped > 0 for media/xlsx
- [x] 4.2 `POST /api/v1/search` with a Metropol-domain query returns hits whose `source_path` is under the corpus (not only fixture) — verify via curl or TestClient against running API

## Workflow follow-up

- After apply: archive/sync (`/opsx-archive`) when ready; next product slice `/answer`.
