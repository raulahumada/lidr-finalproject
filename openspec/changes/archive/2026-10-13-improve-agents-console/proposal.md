# Proposal

## Why

Operators can list Metropol agentic roles on `/agents`, but cannot inspect builtin prompts clearly or add new LLM specialists. A peer-style console that keeps pipeline builtins fixed (code + Jinja) while allowing custom agents in Postgres closes that gap for the delivery demo without turning the product into a generic agent IDE.

## What Changes

- Persist **custom** agent profiles in Postgres (Alembic); expose CRUD under `/api/v1/answer/agents`
- Keep **builtin** pipeline agents read-only in the catalog (Jinja prompt preview for LLM builtins; mutation attempts blocked)
- Enrich catalog responses with prompt preview, builtin vs custom, ladder, knobs
- Add a generic LangGraph `prompt_specialist` node so enabled customs can run on the orchestrator ladder
- Upgrade `/agents` UI to a small studio: inspect builtins, create/edit/delete customs, show flow
- Document API + UI in `AGENTS.md` / `frontend/AGENTS.md`

## Capabilities

### New Capabilities
- `agent-profiles`: Custom agent persistence and CRUD (create/update/delete), reserved builtin keys, effective catalog merge with code-defined specialists

### Modified Capabilities
- `agentic-orchestrator`: Catalog enrichment (prompt preview); ladder may include enabled custom specialist keys via generic node
- `agentic-chat-ui`: `/agents` console supports inspect + custom CRUD + flow (not read-only list only)

## Non-goals

- Editing or deleting builtin agents; rewriting Jinja files from the UI
- Generating new Python node modules from the browser
- LLM supervisor; auth; advanced drag-drop ladder editors
- Changing the sync `POST /answer` path

## Impact

- **backend:** `foundation/persistence` model + Alembic; `domain/graph` store/catalog/orchestrator/build + `prompt_specialist`; `api/routes/answer_agents.py`; tests
- **frontend:** `/agents` studio, `lib/api/agents.ts`, docs
- **Graphify hubs:** `catalog.py`, `AgentsPage`, `grounded_composer` / Jinja loader, persistence models

## Practices check

- **Aligned:** DB via foundation persistence + Alembic; domain logic out of routers; Pydantic create/update schemas; settings for prompt version; absolute `app.` imports
- **Deviations:** Dynamic ladder entries for customs (beyond static `FALLBACK_LADDER`) — needed for CRUD to affect runs; constrained by step budget + legality
- **Risks if ignored:** Mutating builtins; key collisions; unbounded custom loops (mitigate with existing max steps)
