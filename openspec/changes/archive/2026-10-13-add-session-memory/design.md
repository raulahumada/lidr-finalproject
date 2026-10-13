# Design

## Context

See proposal.md — Why. Graphify shows `SessionStore` appends transcript but has **no path** into `intent_framer` / `grounded_composer`; agentic runs still frame with raw `question`. Course `generation/conversation/` feeds history into **generation**; peer Cristian (`.reference/lidr-master` `conversation-memory`) resolves **before retrieval** via deterministic `resolver`, then budgets a memory block behind evidence. Metropol already has Postgres sessions + agentic `session_id`; this change wires memory into the existing linear graph without renaming specialists.

## Goals / Non-Goals

**Goals:**
- Retrieval-first referential resolve + budgeted memory block on agentic path
- Conservative, auditable rewrite (no LLM resolver in v1)
- Layer-clean placement under `generation/conversation/` + graph nodes

**Non-Goals:**
- Peer facts/anchors modules, course compression summarizer, UI work, orchestrator

## Decisions

### 1. Peer-shaped modules, Metropol names
**Choice:** Add `resolver.py` + `budget.py` beside existing `store.py`. Keep graph nodes `intent_framer` / `corpus_fetcher` / `grounded_composer`.

**Alternatives:** LLM rewrite in framer — rejected (peer risk: confident wrong retrieve). Copy peer `query_planner` name — rejected (Metropol naming).

### 2. Hydrate in runner, resolve in intent_framer
**Choice:** `AgenticAnswerRunner` loads last `CONVERSATION_MAX_TURNS` turns into `conversation_window` when `session_id` present. `intent_framer` calls `resolve(question, window)` → `framed_query` + `resolved_question` (+ substituted list for trace).

**Alternatives:** Resolve in API route — rejected (fat router). Resolve only in composer — rejected (does not fix retrieve).

### 3. Referents from prior turns (no facts store yet)
**Choice:** v1 resolver uses last closed turn(s)’ written/resolved questions and light heuristics (Spanish referential markers) mirroring peer conservatism (don’t rewrite self-contained questions). Skip `facts.py` / `anchors.py` until a later change.

**Alternatives:** Full `ConversationFacts` now — deferred to keep v1 shippable.

### 4. Memory block behind evidence budget
**Choice:** `render_memory(window, budget=CONVERSATION_MEMORY_MAX_TOKENS)` injected in `grounded_composer` / prompt user template as optional section. Trim oldest turns first; never cite memory ids.

**Alternatives:** Unlimited history in prompt — rejected. Course multi-message chat API — rejected for grounded JSON+citations path.

### 5. Sync `/answer` rejects `session_id`
**Choice:** HTTP 422 if body includes `session_id` (extra field or explicit schema forbid). Matches peer honesty.

**Alternatives:** Silently ignore — rejected.

### 6. Persist `resolved_question` on append
**Choice:** Extend history turn JSON with optional `resolved_question` when rewritten; schema + SessionStore append.

### 7. Settings
**Choice:** `conversation_max_turns: int = 4`, `conversation_memory_max_tokens: int = 1024` in Settings + `.env.example`.

## Risks / Trade-offs

- [Wrong referent] → Conservative resolver + expose substituted/resolved in trace; prefer no rewrite over bad rewrite
- [Heuristic brittleness vs Metropol vocabulary] → Start with peer-like markers; extend tests with Tenela/cobranzas follow-ups
- [Prompt drift / cache] → Agentic hot path has no Response CAG; sync answer unchanged except 422
- [JSONB growth] → Window for memory is N turns only; full history remains for UI

## Migration Plan

1. Ship resolver/budget + graph wiring behind existing optional `session_id`
2. Alembic not required if JSONB already schemaless for turn keys; update Pydantic `HistoryTurn`
3. Rollback: leave store as-is; framer pass-through if window empty / flag off (default on when session present)

## Open Questions

None — draft open questions resolved in Decisions (422 sync, persist resolved_question, N=4 / 1024 tokens).
