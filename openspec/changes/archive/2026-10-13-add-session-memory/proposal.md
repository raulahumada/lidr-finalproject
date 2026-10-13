# Proposal

## Why

Sessions already store a durable transcript, but each agentic turn still retrieves and answers from the raw follow-up alone. Relative questions (“¿y con Tenela?”) hit the corpus without a referent, so the system can return a well-cited answer to the wrong question. Course history feeds generation; Cristian’s RAG pattern resolves **before retrieval**. Metropol needs that retrieval-first memory now that multi-session UI exists.

## What Changes

- Add conversation-memory helpers under `generation/conversation/`: deterministic `resolver` + `budget`/`render_memory` (window under an evidence-first token ceiling)
- Hydrate last N session turns into agentic graph state when `session_id` is present
- Upgrade `intent_framer` to set `framed_query` / `resolved_question` from the resolver (conservative; no LLM rewrite)
- Inject a non-citable memory block into grounded composer prompts when a window exists
- Persist optional `resolved_question` on closed history turns
- Reject `session_id` on sync `POST /answer` with HTTP 422 (do not pretend that path has memory)
- Settings: `CONVERSATION_MAX_TURNS` (default 4), `CONVERSATION_MEMORY_MAX_TOKENS` (~1024)
- Document memory ≠ transcript ≠ checkpointer in `AGENTS.md`

## Capabilities

### New Capabilities
- `conversation-memory`: Resolve referential questions before retrieve; budgeted recent-turn memory block for synthesis; evidence wins over memory tokens

### Modified Capabilities
- `agentic-answer`: Optional session hydrates window; framing uses resolved query; composer may include memory block; expose rewrite audit in trace/response when applicable
- `chat-sessions`: History turns MAY include `resolved_question` when memory rewrote the query
- `rag-answer`: Sync `POST /answer` SHALL reject `session_id` (422) rather than accept and ignore

## Non-goals

- Full peer facts store + domain anchors (follow-up)
- Course-style LLM compression / rolling summary
- Auth, ownership, session TTL
- Orchestrator / domain supervisor
- Frontend changes (client already sends `session_id`)
- Treating transcript text as citable evidence

## Impact

- **backend:** `generation/conversation/{resolver,budget}.py`, `domain/graph/{state,runner,agents/intent_framer,agents/grounded_composer}`, prompts answer templates, `schemas/session` (+ agentic response fields if needed), `config`/`.env.example`, sync answer route validation, tests, `AGENTS.md`
- **frontend:** none in this change
- **deps:** none new expected

### Graphify notes
Hubs: `SessionStore`, `AgenticAnswerRunner`, `intent_framer`, `grounded_composer`, `corpus_fetcher`. No directed path today from `SessionStore` → composer — this change wires that through state hydration + framing.

## Practices check

- **Aligned:** Thin routers; memory logic in `generation/conversation` + graph nodes; runner as conductor for hydrate/append; settings via `config.py`; typed schemas; unit tests for resolver/budget
- **Deviations:** v1 omits peer facts/anchors (minimal usable slice); Metropol node names kept (`intent_framer` not `query_planner`)
- **Risks if ignored:** Aggressive LLM rewrite → confident wrong retrieve; unbounded memory block displaces evidence; accepting `session_id` on sync without memory lies to callers
