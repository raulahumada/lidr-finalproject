# Design

## Context

See proposal.md — Why. Today `run_ingest()` lives only behind the CLI (`app/ingestion/run_ingest.py`); Graphify shows no edge to `api_router`. Frontend already has AppShell + `/search` as the natural post-ingest check. Course `session_16` exposes ingest/index as thin 202 + poll routers; we mirror that shape without adopting DataCatalog or durable JobsRepository.

## Goals / Non-Goals

**Goals:**
- Bridge CLI orchestrator to HTTP without duplicating parse/chunk/embed
- Operator-visible run lifecycle (start → poll → summary) + static corpus stats
- Astryx console page that matches `/search` density

**Non-Goals (design-level):**
- Durable job rows / queue workers
- Multiprocess-safe job locks beyond a single Uvicorn worker
- Streaming per-file progress (summary-at-end is enough for v1)

## Decisions

1. **Reuse `ingestion.orchestrator.run_ingest` as the only batch engine**  
   HTTP and CLI share the same function + `IngestSummary`.  
   *Alt:* new service that reimplements walk/parse — rejected (parallel island; Graphify already hubs on orchestrator).

2. **Router thin at `api/routes/ingest.py` + schemas `schemas/ingest.py`**  
   Layer map (`docs/python-best-practices.md`): `api` → dependencies → orchestrator (`ingestion`) + `foundation/persistence` + `generation/rag` embedder. No parsers imported from routes.  
   *Alt:* put HTTP inside `ingestion/` — rejected (course + local practices keep transport in `api/`).

3. **In-process job registry (dict + lock), pattern like `GraphActivityLog`**  
   States: `queued|running|completed|failed`. Store summary/errors on completion. Lost on Uvicorn reload.  
   *Alt:* Alembic `ingest_jobs` table (course JobsRepository) — deferred; demo + single operator don’t need F5 mid-run durability yet.

4. **Single concurrent run → HTTP 409**  
   Prevents double OpenAI spend / force races.  
   *Alt:* queue — more moving parts than v1 needs.

5. **Background execution via FastAPI `BackgroundTasks` (or short-lived thread equivalent to agentic start)**  
   `POST` returns 202 immediately with `run_id`.  
   *Alt:* sync blocking POST — bad UX for full Metropol corpus.

6. **No HTTP `root` override; only `force: bool`**  
   Root always from settings `CORPUS_ROOT`. CLI keeps `--root`.  
   *Alt:* allow path in body — deferred until auth exists.

7. **`GET /ingest/stats` via ChunkStore counts + settings metadata**  
   Documents/chunks counts from DB; expose configured root string + allowlist for the UI. No filesystem walk.  
   *Alt:* walk CORPUS_ROOT for “files pending” — expensive and noisy with media skips.

8. **Frontend `/ingest` mirrors `/search`**  
   Typed client `lib/api/ingest.ts`, poll ~1.2s, SideNav near search, home CTA. Astryx workflow only.

9. **Capability split:** delta `corpus-ingest` (HTTP contract) + new `ingest-console-ui` (screen) — same split as `semantic-search` / `search-console-ui`.

## Layer map

| Piece | Layer |
|-------|--------|
| `api/routes/ingest.py` | api (transport) |
| `schemas/ingest.py` | schemas / contracts |
| In-process job registry | foundation-adjacent helper under `ingestion/` or `api` support module — prefer `app/ingestion/jobs.py` so api stays thin |
| `orchestrator.run_ingest` | ingestion (existing) |
| Embedder / ChunkStore | generation/rag + foundation (existing) |

**Tension:** job registry is ephemeral infra; keeping it next to ingestion avoids teaching `api` to own state machines. Acceptable vs putting it in foundation (no other job infra yet).

## Risks / Trade-offs

- [Reload mid-run loses poll state] → Mitigation: document; CLI remains source of truth for long ops; run completes in background process until worker dies
- [Multi-worker Uvicorn: two processes both accept runs] → Mitigation: document single-worker local default; 409 only within one process
- [Long embed run ties a worker] → Mitigation: BackgroundTasks; accept teaching-scale latency; no Celery
- [Open API without auth] → Mitigation: localhost demo; auth is the next planned change

## Migration Plan

1. Deploy backend routes (additive); no DB migration
2. Ship frontend page; existing CLI users unchanged
3. Rollback: remove routes/page; index data untouched

## Open Questions

None for this change (defaults locked in approved draft).
