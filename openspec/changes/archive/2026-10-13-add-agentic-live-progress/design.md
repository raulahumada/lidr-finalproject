# Design

## Context

See proposal. Sync agentic API and chat UI already exist. Peer/course pattern: in-process activity log + graph stream updates + start/progress. Our runner is sync (`invoke`); we adapt with `stream` in a background thread.

## Goals / Non-Goals

**Goals:**
- Start returns immediately; progress narrates Metropol nodes; front polls and animates steps.
- Keep sync POST and resume working.

**Non-Goals:**
- Token streaming, Redis activity, Postgres checkpointer, peer session filters.

## Decisions

1. **In-process `GraphActivityLog`** — same as peer for single-worker local; document reload loss with MemorySaver.
2. **`threading.Thread` + strong set** — sync FastAPI stack; avoid blocking the request on `stream`. Hold thread refs until done.
3. **`graph.stream(..., stream_mode="updates")`** — append `describe_node` per update; then inspect checkpointer state / interrupts for terminal status (reuse `_to_response` logic).
4. **Metropol labels in Spanish** for UI (intent, corpus, composer, guard, gate).
5. **Front poll 1200ms** — match Cristian; abort on unmount / new submit.
6. **ChatToolCalls** for live steps — map known pipeline nodes to pending/running/complete from `activity`.

## Risks / Trade-offs

- **[Risk] Thread GC mid-run** → Strong `_BACKGROUND_THREADS` set + done callback discard.
- **[Risk] Multi-worker inconsistency** → Accept single-process; document.
- **[Risk] Progress 404 after reload** → Same MemorySaver caveat; UI already handles 404.
- **[Trade-off] Sync stream in thread vs async astream** → Matches current sync deps/retriever without rewriting to async SQLAlchemy.

## Migration Plan

1. Land backend start/progress + tests.
2. Switch front hot path to start+poll.
3. Smoke completed and pause+resume.
4. `graphify update .`

Rollback: front can revert to `postAgenticAnswer`; leave start/progress unused.

## Open Questions

None.
