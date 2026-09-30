# OpenSpec history

Changelog of promoted changes in this monorepo.

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
