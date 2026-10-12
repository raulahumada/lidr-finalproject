# Proposal

## Why

`POST /api/v1/answer` already delivers grounded Metropol Q&A in one shot, but the course path needs an **auditable multi-step graph** (specialists + optional human pause) before the frontend. Agentic answer is the next product slice after prompts v2.

## What Changes

- Add `POST /api/v1/answer/agentic` and `POST /api/v1/answer/agentic/{thread_id}/resume`.
- Add a LangGraph `StateGraph` under `backend/app/domain/graph/` with Metropol-named specialists + conditional human gate.
- Reuse retrieve / prompts v2 / citation helpers from the existing answer path; keep sync `/answer` unchanged.
- Add `langgraph` dependency, typed state, `MemorySaver` checkpointer (v1), tests, and `AGENTS.md` curl docs.

## Capabilities

### New Capabilities
- `agentic-answer`: Multi-step LangGraph Q&A over Metropol corpus with agent trace and optional human escalation.

### Modified Capabilities
- (none — `rag-answer` requirements stay; agentic is a parallel endpoint that reuses generation pieces)

## Non-goals

- Copying Cristian or course-estimator agent **names**
- Frontend / agent console / progress polling UI
- LLM supervisor that picks the next node at runtime (v1 = fixed pipeline)
- Orchestrator hub + `AsyncPostgresSaver` (deferred follow-up)
- CAG on the agentic hot path (optional cache of final result later)
- Hybrid retrieve, advanced decompose, multi-turn memory, multi-provider LLM

## Impact

- **Surface:** backend only.
- **Code:** `domain/graph/` (state, agents, build, gate, runner), `api/routes/answer_agentic.py`, schemas, `dependencies.py` / lifespan, `requirements.txt`, tests, `AGENTS.md`.
- **Reuse (Graphify hubs):** `AnswerService` / prompt render / `context_blocks`, `SemanticRetriever`, `ChatClient`, `get_settings()`.
- **Deps:** `langgraph`; checkpointer v1 = in-process `MemorySaver` (resume works until process restart).

## Practices check

- **Aligned:** thin routers; graph + gate in `domain/`; reuse retriever/prompts; `get_settings()`; layer rules from `docs/python-best-practices.md`; schemas for request/response.
- **Deviations:** fixed pipeline (not S14 LLM supervisor); `MemorySaver` instead of Postgres checkpointer; Metropol node names (not peer verbatim). Follow-ups documented in draft.
- **Risks if ignored:** duplicating `/answer` generation logic; gate that always interrupts; importing generation siblings across pipelines; losing interrupt state on reload without documenting MemorySaver limits.

## Graphify notes

- Hubs to extend: `AnswerService`, `SemanticRetriever`, `ChatClient`, `render_answer_prompts`, `fit_to_budget` / `ContextBlock`, answer routes/deps.
- New island: `domain/graph/*` (expected); wire via runner + deps, not a second retrieve stack.
