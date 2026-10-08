# Tasks

## 1. Dependencies and chunking module

- [x] 1.1 Add `langchain-text-splitters` and `tiktoken` to `backend/requirements.txt` and install — verify imports succeed
- [x] 1.2 Implement `normalize_text` + `chunk_document` with recursive default (512 / ~80 overlap) and Markdown header path under `generation/rag/` — verify unit tests for empty text, long prose (>1 chunk), md section boundaries
- [x] 1.3 Remove or replace legacy paragraph-only `chunk_text` callers — verify no production import of the old behavior remains (tests may keep a thin wrapper if needed)

## 2. Ingest wiring

- [x] 2.1 Update `ingestion/orchestrator` to use `chunk_document` and persist `strategy` / `section` in chunk metadata — verify orchestrator test with mock embedder still passes
- [x] 2.2 Document re-ingest `--force` after chunking upgrade in `AGENTS.md` — verify commands match

## 3. Verification

- [x] 3.1 `python -m pytest -q` for chunking + ingest tests — verify green
- [x] 3.2 Re-ingest Metropol with `--force` and smoke `POST /api/v1/search` — verify hits return and chunk metadata includes strategy when inspected in DB or response metadata

## Workflow follow-up

- Archive/sync when done; next product slice `/answer` (or evals if measuring chunking A/B).
