# Design

## Context

Sync `POST /api/v1/answer` already owns retrieve → budgeted blocks → prompts v2 → LLM → citation filter via `AnswerService` (Graphify hubs: `AnswerService`, `SemanticRetriever`, `ChatClient`, `context_blocks`). Course S13/S14 and peer lidr-master show LangGraph under `domain/graph/` with least privilege and `interrupt()`. This change adds a parallel agentic path without replacing sync answer. See proposal.md for motivation.

## Goals / Non-Goals

**Goals:**
- Fixed specialist pipeline + conditional `interrupt` with HTTP 200/202 + resume.
- Metropol node names; reuse generation pieces from existing hubs.
- Thin API; graph logic in `domain/graph/`.

**Non-Goals:**
- Orchestrator hub, LLM supervisor, Postgres checkpointer (follow-ups).
- Frontend, CAG on hot path, multi-turn memory.

## Decisions

1. **Layout:** `backend/app/domain/graph/` — `state.py`, `agents/` (`intent_framer`, `corpus_fetcher`, `grounded_composer`, `source_guard`), `gate.py` (`escalation_gate`), `build.py`, `runner.py`. API: `api/routes/answer_agentic.py`. Matches course `domain/graph` shape; domain = Metropol Q&A.

2. **Control flow v1:** linear `START → intent_framer → corpus_fetcher → grounded_composer → source_guard → escalation_gate → END`. Alternative considered: peer orchestrator hub — deferred to keep v1 small while still teaching specialists + gate.

3. **Least privilege:** only `corpus_fetcher` calls `SemanticRetriever`. Others read/write state only. Optional privilege frozenset mirror (course/peer) if cheap; not a second tool sandbox in v1.

4. **Reuse vs duplicate:** extract or call shared helpers from answer path (`fit_to_budget` / blocks, prompt render, citation mapping) rather than a second prompt stack. Prefer small shared functions over importing `AnswerService` wholesale if CAG side effects get in the way; if calling `AnswerService` internals, skip Response CAG on agentic hot path.

5. **Checkpointer:** process-scoped `MemorySaver` in app lifespan / deps. Resume works until process restart. Alternative `AsyncPostgresSaver` deferred (peer/course production path).

6. **Gate:** pure `review_reasons(state)` first; call `interrupt()` only when non-empty (peer discipline). Triggers: no evidence, `citations_valid is False`, confidence below settings threshold. HTTP: 202 + `thread_id` on interrupt; resume endpoint maps approve/reject/adjust.

7. **Settings:** confidence threshold + maybe max k already on answer; add agentic-specific knobs only if needed (`AGENTIC_CONFIDENCE_THRESHOLD`). `get_settings()` only.

8. **Layers:** `api` → runner/deps; `domain/graph` → foundation LLM + generation/rag + schemas; no api imports inside graph. Aligns with `docs/python-best-practices.md`.

## Risks / Trade-offs

- **[Risk] MemorySaver loses paused threads on reload** → Document in AGENTS.md; follow-up Postgres saver.
- **[Risk] Duplicated generation logic drift from `/answer`** → Share helpers; tests for citations/no-evidence on both paths where practical.
- **[Risk] Gate always interrupts** → Unit-test empty reasons fall through; only configured triggers.
- **[Risk] Fixed pipeline looks “less multiagente” than S14** → Accept for v1; deferred orchestrator/LLM supervisor recorded in draft.

## Migration Plan

1. Add `langgraph`, implement graph + routes, wire router.
2. Deploy locally with existing Postgres/Redis unchanged (Redis not required for agentic v1).
3. Rollback: remove route mount / feature unused; sync `/answer` unaffected.

## Open Questions

None blocking — CAG on agentic final result and `/start`+progress remain follow-ups.
