# Design

## Context

See proposal.md — Why. Today `GET /answer/agents` returns a code-defined catalog (`catalog.py`); `/agents` is read-only. Builtins (orchestrator + Metropol specialists) and Jinja prompts (`foundation/prompts/answer/{version}/`) already exist. Conversation sessions already use Postgres + Alembic in `foundation/persistence`.

Graphify hubs to extend: `catalog.py` / `agent_catalog()`, `answer_agents` router, `AgentsPage`, `orchestrator` / `build_agentic_answer_graph`, prompt loader used by `grounded_composer`.

## Goals / Non-Goals

**Goals:**
- Custom agent rows in Postgres with full CRUD
- Unified catalog: builtins (immutable) + customs
- Customs that are enabled participate in the agentic ladder via one generic LLM node
- Console UX for inspect builtins + manage customs + show flow

**Non-Goals:**
- Builtin mutation; writing `.j2` from API
- Per-custom Python modules; LLM supervisor

## Decisions

### 1. Builtins stay in code; customs only in DB
**Choice:** Builtin metadata remains the hard-coded allowlist in `catalog` (or equivalent). `agent_profiles` table stores **only** customs.

**Alternatives:** Seed builtins into DB as editable — rejected (user asked builtins non-editable; Jinja remains SSOT for composer prompt).

### 2. Effective prompt
**Choice:** Builtin LLM agents expose `prompt_preview` by reading allowlisted Jinja source under `foundation/prompts`. Customs expose `system_prompt` from DB. No override column for builtins.

### 3. Generic `prompt_specialist` node
**Choice:** One LangGraph node runs any enabled custom profile (system prompt from DB + bounded user context: question / framed query / optional short evidence summary). Output: short text note into state (e.g. `custom_notes` / trace), **not** replacing `grounded_composer` citations contract.

**Alternatives:** Dynamic graph compile per custom — rejected as heavier. Customs replace composer — rejected (breaks grounding).

### 4. Ladder placement
**Choice:** Default insert for enabled customs: **after `corpus_fetcher`, before `grounded_composer`**. Builtins keep legal order; customs are optional LLM steps with legality “once per key”. Step budget still applies.

**Alternatives:** After composer — deferred; configurable free reorder of builtins — out of scope (only enable/disable customs + fixed insert slot).

### 5. API shape
**Choice:** Extend existing `/answer/agents` router:
- `GET` list (enriched)
- `GET /{key}` detail
- `POST` create custom
- `PATCH /{key}` update custom only
- `DELETE /{key}` delete custom only  
Builtin mutation → HTTP 405 or 422 with clear detail. Key collision with builtin on POST → 409.

### 6. UI
**Choice:** Single `/agents` page: list with builtin/custom badge, detail panel (read-only vs form), create form, flow section (ladder string + agents). Astryx only.

## Risks / Trade-offs

- [Custom agents add latency/cost] → enabled flag + existing `agentic_orchestrator_max_steps`
- [Custom output confuses composer] → customs write side notes/trace only; composer remains citation owner
- [Reserved key spoofing] → reject POST keys in builtin set
- [Jinja path escape on preview] → allowlist under `foundation/prompts` only

## Migration Plan

1. Alembic `agent_profiles` table (empty).
2. Deploy API + generic node + catalog merge (behavior unchanged if no customs).
3. Ship `/agents` studio.
4. Rollback: drop feature flag or ignore customs table; revert UI to list-only.

## Open Questions

None — draft defaults locked (builtins read-only; customs in DB; insert after corpus_fetcher).

## Practices check

- Persistence in foundation + Alembic; store/domain in `domain/graph`; thin routes; Create/Update schemas; no SQL in routers.
