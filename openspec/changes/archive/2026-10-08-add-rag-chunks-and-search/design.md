# Design

## Context

See `proposal.md` for why. `local-pgvector` already provides Postgres 16 + extension `vector` and `DATABASE_URL`. Course `session_16` Session 8 shape (`.reference/ai-engineering/ai-service/`): Alembic `documents`/`chunks`, thin `POST /search`, `SemanticRetriever`, no HNSW yet. Host shell is **macOS/bash** (not PowerShell).

Layer mapping (`docs/python-best-practices.md` + course form):

| Module | Layer | May depend on |
|--------|--------|----------------|
| `app/config.py` | config | — |
| `app/foundation/persistence/` | foundation | config |
| `app/schemas/search.py` (or under `schemas/`) | schemas | config |
| `app/generation/rag/` (embedder, retriever, seed helpers) | generation/rag | config, foundation, schemas |
| `app/dependencies.py` | composition root | wiring only |
| `app/api/routes/search.py` | api | dependencies, schemas |

No domain conductor yet — acceptable; `/answer` will introduce it. No cross-imports between future `generation/*` siblings.

## Goals / Non-Goals

**Goals:**
- Reproducible schema via Alembic for `documents` / `chunks`.
- Semantic search over cosine distance with OpenAI `text-embedding-3-small` (1536-d).
- Fixture seed CLI for local demo without Metropol files.
- Ops docs for migrate + seed + curl search on macOS.

**Non-Goals (design-level):**
- Async SQLAlchemy everywhere if sync session is enough for first slice (prefer simplest working stack; document choice).
- Multi-provider embeddings or prompt versioning.
- HTTP write/ingest API (CLI seed only this change).

## Decisions

1. **Alembic rooted at `backend/`**  
   - Why: matches course `ai-service/alembic` placement relative to the Python app.  
   - Alternative: root monorepo Alembic — rejected; only backend owns the schema.

2. **Tables `documents` + `chunks` (generic names, not `budget_*`)**  
   - Why: course S8 shape without estimator domain.  
   - Embedding `Vector(1536)` nullable; FK CASCADE; JSONB metadata; no vector index yet.

3. **Sync SQLAlchemy + `psycopg` for v1**  
   - Why: smallest path for migrate/seed/search; course uses async later complexity we can adopt when needed.  
   - Alternative: full async engine now — defer unless apply hits a hard conflict with FastAPI patterns.

4. **OpenAI embeddings only (`text-embedding-3-small`)**  
   - Why: same space as course S8; changing model later requires re-embed.  
   - Config: `openai_api_key`, `embedding_model`, fixed dim 1536 in code/constants.

5. **`POST /api/v1/search` under existing prefix**  
   - Why: monorepo contract; course bare `/search` is the pattern, not the path.  
   - `k` default 5, bounds e.g. 1–50 → 422 outside.

6. **CLI seed module (`python -m app…` or `backend/scripts/seed_fixture.py`)**  
   - Why: no HTTP write surface yet; Option A from draft.  
   - Fixture text can live under `backend/data/fixtures/` (small, commit-safe) or inline constants.

7. **503 when key missing; 200 empty results when DB empty**  
   - Why: mirrors course search semantics; avoids fake rankings.

8. **Composition via `dependencies.py`**  
   - Why: routers stay thin; retriever injected with `Depends`.

## Risks / Trade-offs

- **[Risk] Sync DB calls block event loop** → Mitigation: acceptable for local/dev slice; note follow-up to async if latency hurts.
- **[Risk] Embedding API cost/failures on seed/search** → Mitigation: clear 503/500 messages; seed is opt-in CLI.
- **[Risk] Dim mismatch if model changes** → Mitigation: pin model+dim in settings/constants; document re-ingest.
- **[Trade-off] No HNSW** → Seq scan fine for fixture/small corpus; index later with eval.
- **[Trade-off] Fixture ≠ Metropol** → Unblocks demo; real corpus is next change with user path.

## Migration Plan

1. Install deps → configure `backend/.env` (`DATABASE_URL`, `OPENAI_API_KEY`).  
2. `docker compose up -d` (existing) → `alembic upgrade head` from `backend/`.  
3. Run seed CLI → `POST /api/v1/search` smoke.  
4. Rollback schema: `alembic downgrade -1` (or base); data wipe via Compose volume only if intentional.

## Open Questions

None blocking apply. Deferred: Metropol corpus path, HTTP ingest, hybrid/HNSW, `/answer`.
