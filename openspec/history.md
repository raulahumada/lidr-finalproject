# OpenSpec history

Changelog of promoted changes in this monorepo.

## 2026-10-08 — `add-rag-chunks-and-search`

**Status:** archived → `openspec/changes/archive/2026-10-08-add-rag-chunks-and-search/`  
**Surface:** backend  
**Synced to:** `openspec/specs/rag-chunks/spec.md`, `openspec/specs/semantic-search/spec.md`

### What landed

- Alembic under `backend/` with migration for `documents` / `chunks` (`Vector(1536)`, no HNSW).
- Layers `foundation/persistence` + `generation/rag` + thin `POST /api/v1/search`.
- OpenAI `text-embedding-3-small` settings; fixture seed CLI; pytest for search contract.
- Ops docs in `AGENTS.md` (migrate, seed, curl); macOS bash sync-reference script.

### Why

First usable RAG slice: persist + semantic retrieve over pgvector, without answer generation or agents yet.

### Follow-ups (out of this change)

- Ingest real Metropol Fintech corpus (user path).
- `POST /answer` with citations; then multiagent orchestration.
- Do not commit `backend/.env`.

## 2026-09-30 — `add-local-pgvector`

**Status:** archived → `openspec/changes/archive/2026-09-30-add-local-pgvector/`  
**Surface:** backend + repo root (Compose)  
**Synced to:** `openspec/specs/local-pgvector/spec.md`

### What landed

- Root `docker-compose.yml`: Postgres **16** via `pgvector/pgvector:pg16`, volume `pgdata`, host port `5432`, healthcheck `pg_isready`.
- Credentials via root `.env` (from `.env.example` placeholders); Compose interpolates `POSTGRES_*` / `PGADMIN_*` — no hardcoded passwords in YAML.
- Init script `docker/init-vector.sql` enables extension `vector` on first volume create.
- pgAdmin (`dpage/pgadmin4`) on host port `5050`; DB host from inside Compose = `postgres`.
- Backend `Settings.database_url` + `backend/.env.example` (`DATABASE_URL` for host-run API).
- Ops docs in `AGENTS.md` (bring-up, verify extension, pgAdmin connection fields).


### Why

Unblocks the next RAG slice (chunks/embeddings) without inventing another datastore; aligns PG major with the course reference image family.

### Follow-ups (out of this change)

- Alembic / `chunks` table, driver usage in app, ingest + `/search`.
- Do not commit `backend/.env`.
