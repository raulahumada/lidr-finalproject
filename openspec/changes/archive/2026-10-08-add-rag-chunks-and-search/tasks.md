# Tasks

## 1. Dependencies and settings

- [x] 1.1 Add to `backend/requirements.txt`: SQLAlchemy, Alembic, `psycopg[binary]`, `pgvector`, `openai` (version floors with `>=`) — verify `pip install -r requirements.txt` succeeds in the backend venv
- [x] 1.2 Extend `Settings` with `openai_api_key`, embedding model default `text-embedding-3-small`, and document `DATABASE_URL` + new keys in `backend/.env.example` — verify `get_settings()` loads the new fields without requiring a real key at import time

## 2. Alembic schema (`rag-chunks`)

- [x] 2.1 Initialize Alembic under `backend/` (`alembic.ini`, `alembic/env.py` reading URL from settings / `DATABASE_URL`) — verify `cd backend && alembic history` runs
- [x] 2.2 Add migration creating `documents` + `chunks` (FK CASCADE, `embedding Vector(1536)` nullable, JSONB metadata, relational indexes; `CREATE EXTENSION IF NOT EXISTS vector`; no HNSW) — verify `alembic upgrade head` against Compose Postgres and tables exist via `psql`/`\dt`
- [x] 2.3 Implement `app/foundation/persistence/` (engine/session factory, ORM models, minimal repo helpers) using `get_settings().database_url` — verify a small script or test can open a session and select from `chunks`

## 3. RAG retrieval + search API (`semantic-search`)

- [x] 3.1 Add `app/generation/rag/` embedder + semantic retriever (embed query → cosine rank → top-k); keep SQL/embedding out of routers — verify unit/integration call returns `[]` on empty DB when key is present (mock embed if needed)
- [x] 3.2 Add Pydantic search request/response schemas and thin `POST` route registered at `{api_prefix}/search` with `dependencies.py` wiring; 503 without key, 422 for bad `k`, 200 empty results — verify with `TestClient` (happy/empty + 422 + 503)
- [x] 3.3 Document endpoint in OpenAPI by ensuring route + `response_model` are registered — verify `/docs` lists `POST /api/v1/search`

## 4. Fixture seed CLI

- [x] 4.1 Add documented CLI/module that inserts one fixture document + chunks with embeddings (commit-safe fixture text; requires API key) — verify after migrate+seed that `chunks` has at least one non-null embedding
- [x] 4.2 Smoke `POST /api/v1/search` against seeded DB returns ≥1 hit for a related query — verify via curl or TestClient against running stack

## 5. Docs

- [x] 5.1 Update `AGENTS.md` with macOS/bash steps: `alembic upgrade head`, seed command, example curl to `/api/v1/search`, required env vars — verify commands match actual paths/module names
- [x] 5.2 Mark draft `openspec/drafts/add-rag-chunks-and-search.md` as promoted to this change — verify Status checkbox / promotion line present

## Workflow follow-up

- After apply + verify: `/opsx-apply` completion → archive/sync specs when ready (`/opsx-archive` or sync skill).
- Next product slice (out of this change): Metropol corpus path + real ingest; then `/answer`.
