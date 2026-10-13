# Design

## Context

See proposal.md — Why. Today `build_agentic_answer_graph` is a linear `StateGraph` (Graphify hub). Course S14 uses a star supervisor; Cristian uses a deterministic orchestrator ladder + catalog/`GET /config` + `/agents` UI. Metropol specialists and human gate already exist; this change rewires topology and adds domain + catalog surfaces.

## Goals / Non-Goals

**Goals:**
- Star topology with Metropol-named specialists
- Auditable deterministic routing + step budget
- Domain tag + catalog API + `/answer` + `/agents` UI

**Non-Goals:**
- LLM supervisor; domain-LLM agents; re-query loops; DB model profiles

## Decisions

### 1. Star + Command(goto)
**Choice:** `START → orchestrator`; specialists return to orchestrator; finish path → `escalation_gate` → END.

**Alternatives:** Keep linear edges — rejected (not multiagent). Full LLM supervisor — deferred.

### 2. Deterministic ladder (peer-shaped)
**Choice:** Order `intent_framer → corpus_fetcher → grounded_composer → source_guard → finish(gate)` with legality/precondition checks and `AGENTIC_ORCHESTRATOR_MAX_STEPS`.

**Alternatives:** Always identical to today’s line via static edges only — rejected (no hub/history).

### 3. Domain as tag
**Choice:** Heuristic classifier (keywords / light rules on question+window) + optional override on request. Bias: optional query prefix / composer system hint. No separate LangGraph nodes per domain in v1.

### 4. Catalog module
**Choice:** `domain/graph/catalog.py` drives `GET /api/v1/answer/agents`. Frontend `/agents` and labels consume it only.

### 5. UI placement
**Choice:** New `/agents` route + SideNav item; `/answer` gets domain select + routing display in existing progress/trace panels. Astryx only.

### 6. Settings
**Choice:** `agentic_orchestrator_max_steps` in Settings / `.env.example`. Catalog response MAY echo effective knobs for the console (read-only in v1).

## Risks / Trade-offs

- [Infinite hub loops] → step budget + legality “already ran”
- [Cosmetic multiagent] → require routing_history in API tests
- [Domain misfire] → override in UI; conservative `general` fallback
- [Catalog drift] → single server module only

## Migration Plan

1. Ship star build behind same agentic endpoints (behavior sequence ≈ today’s line for happy path).
2. Add catalog + domain fields (backward compatible: new optional request field, new response fields).
3. Roll out `/agents` UI.
4. Rollback: revert `build.py` to linear if needed; clients ignore unknown fields.

## Open Questions

None — draft open questions resolved (UI `/agents`, domain override yes, no re-query loops).
