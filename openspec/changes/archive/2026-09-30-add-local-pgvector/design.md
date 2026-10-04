# Design

## Context

See `proposal.md` for why. Today the monorepo has FastAPI under `backend/` with no database. Course `session_16` uses `pgvector/pgvector:pg16` as the AI service datastore; we mirror that major version and image family. The API runs on the host (`uvicorn`), so the DB must be reachable on localhost.

Layer mapping (`docs/python-best-practices.md`): this change is **infra + settings** only. It prepares for a future `foundation/persistence/` module but does **not** create that package or Alembic yet — no tension with “no SQL in routers” because there is no DB access code in routes.

## Goals / Non-Goals

**Goals:**
- Compose services: Postgres 16 + pgvector (durable volume, healthy, port published) **and** pgAdmin for local browsing.
- Extension `vector` enabled on first init.
- `database_url` in Settings + `.env.example`; local `.env` updated for the developer.
- Ops docs in `AGENTS.md` (DB + pgAdmin URL/login).

**Non-Goals:**
- Application connection pool, ORM models, migrations, RAG tables.
- Redis, second Postgres, containerizing backend/frontend.
- Production-hardened pgAdmin (auth SSO, TLS) — local defaults only.
- Pinning exact pgvector patch beyond what the `pg16` image ships (image tag is the contract).

## Decisions

1. **Image `pgvector/pgvector:pg16`**  
   - Why: aligns with course; user confirmed stay on PG16 (not 17/18).  
   - Alternative: `0.8.6-pg18` — rejected for this change.

2. **Service name `postgres`, DB `entrega_lidr`, volume `pgdata`**  
   - Why: clearer in a small monorepo than course’s `vector-db` / `estimator`.  
   - Alternative: rename to `vector-db` — unnecessary coupling to course names.

3. **Publish `5432:5432`**  
   - Why: host-run API.  
   - Alternative: course strict (no publish) + only in-network AI container — not our layout yet.  
   - Note: if host already has Postgres on 5432, bind fails; document checking the port; optional later remap (e.g. 5433) if needed.

4. **Init via `docker/init-vector.sql` mounted to `docker-entrypoint-initdb.d`**  
   - Why: extension ready on first volume create.  
   - Alternative: manual `CREATE EXTENSION` in apply only — easy to forget.

5. **Credentials via root `.env` (Compose interpolation), never hardcoded in YAML**  
   - `.env.example` documents variable names with placeholders; local `.env` is gitignored. Not for production.

6. **No Python DB driver in this change**  
   - Why: nothing in app connects yet. Driver lands with persistence/RAG.  
   - Verify with `docker compose exec` + `psql`.

7. **pgAdmin via `dpage/pgadmin4` on host port `5050`**  
   - Why: visual admin without installing a desktop client; same Compose stack.  
   - Connects to hostname `postgres` on the Compose network (not `localhost` from inside the container).  
   - `PGADMIN_*` via root `.env`; use a deliverable email domain (pgAdmin rejects reserved domains like `.local`).  
   - Optional: pre-register server via `PGADMIN_SERVER_JSON_FILE` / servers.json — nice-to-have; manual “Register Server” is acceptable if simpler. Prefer auto-register if low-cost.  
   - Alternative: only `psql` — rejected; user asked for pgAdmin.

## Risks / Trade-offs

- **[Risk] Host port 5432 conflict** → Mitigation: document; if conflict, change host mapping in a follow-up.
- **[Risk] Host port 5050 conflict** → Mitigation: document; remap pgAdmin host port if needed.
- **[Risk] Init scripts only run on empty volume** → Mitigation: document that extension is ensured on first create; for existing empty misconfigured volumes, run `CREATE EXTENSION` once.
- **[Trade-off] Published DB + pgAdmin ports** → Acceptable for local AI Engineering delivery; not for production exposure.
- **[Trade-off] Local passwords live in gitignored `.env`** → Dev-only; never reuse in prod; keep YAML free of secrets for scanners.

## Migration Plan

- Add files → `docker compose up -d` → wait healthy → verify extension.  
- Rollback: `docker compose down` (keep volume) or `down -v` to wipe data. No app schema to migrate.

## Open Questions

None blocking apply.
