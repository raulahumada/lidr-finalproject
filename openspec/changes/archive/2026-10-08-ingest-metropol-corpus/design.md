# Design

## Context

See `proposal.md` for why. Store + search already land (`rag-chunks`, `semantic-search`). User corpus lives at  
`/Users/rahumada/Documents/Corpus/Metropol Fintech - Omnicanalidad (Agentes)` (~pdf/docx heavy; also xlsx/mp4/png to skip).

Course shape (`session_16` `app/ingestion/`): filesystem loader + `ParserRegistry` + orchestrator. Catalog/jobs deferred.

Layer map (`docs/python-best-practices.md`):

| Module | Layer | Notes |
|--------|--------|--------|
| `config` | config | `corpus_root`, extensions CSV |
| `foundation/persistence` | foundation | existing `ChunkStore` (+ delete-by-path helper if needed) |
| `generation/rag` | generation | embedder + new simple chunker |
| `ingestion/*` | ingestion | may use foundation + generation/rag (course allows ingestion → rag) |
| CLI `__main__` | entry | not under `api/` |

## Goals / Non-Goals

**Goals:**
- CLI ingest allowlisted files into existing tables with embeddings.
- Skip unsupported types safely; idempotent by `source_path`.
- Ops docs for macOS/bash.

**Non-Goals:**
- HTTP ingest, catalog YAML, PII, xlsx parsers, OCR/video.

## Decisions

1. **Capability `corpus-ingest` separate from `rag-chunks`**  
   - Why: store schema vs batch ingest lifecycle.  
   - Alternative: extend `rag-chunks` — rejected to keep specs focused.

2. **Default `CORPUS_ROOT` empty; example path only in docs / developer `.env`**  
   - Why: no personal paths in committed code.  
   - Dev value (local, gitignored): Metropol subfolder under Documents/Corpus.

3. **Allowlist default `pdf,docx,txt,md`**  
   - Why: highest narrative value; matches draft.  
   - xlsx deferred.

4. **Parsers: txt/md (stdlib), pdf (`pypdf`), docx (`python-docx`)**  
   - Why: common, enough for v1.  
   - Failures per file → count as failed, continue run.

5. **Chunking: paragraph-first, fallback fixed-size (~800 chars, small overlap)**  
   - Why: simple; good enough before eval-driven tuning.

6. **Idempotency: skip if `source_path` exists; `--force` deletes doc (CASCADE chunks) then reinsert**  
   - Why: safe default; explicit rebuild.

7. **`source_path` stored as path relative to `CORPUS_ROOT` when possible**  
   - Why: portable across machines; absolute fallback if needed.

8. **No new HTTP routes**  
   - Why: CLI matches course offline ingest spirit for first pass.

## Risks / Trade-offs

- **[Risk] Embedding cost on large PDF set** → Mitigation: allowlist + progress logs; operator can dry-run count later if we add `--dry-run` (optional nice-to-have in tasks).
- **[Risk] Scanned PDFs with no text layer** → Mitigation: empty extract → fail/skip that file with message; OCR out of scope.
- **[Risk] Sync embed loop slow** → Acceptable for batch CLI; same sync stack as search v1.
- **[Trade-off] No catalog** → Faster ship; revisit if multiple roots/sources needed.

## Migration Plan

1. Install new deps → set `CORPUS_ROOT` + `OPENAI_API_KEY` in `backend/.env`.  
2. DB already migrated (`alembic upgrade head`).  
3. Run CLI → verify counts → `POST /search` with a Metropol question.  
4. Rollback data: delete rows / `--force` selective; no schema migration expected.

## Open Questions

None blocking (draft proposals locked: Metropol subfolder, skip+`--force`, no xlsx).
