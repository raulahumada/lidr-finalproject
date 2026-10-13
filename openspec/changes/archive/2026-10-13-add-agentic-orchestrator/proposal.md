# Proposal

## Why

The Metropol agentic path is still a hard-wired line (`intent_framer → … → gate`). That is multi-*step*, not multi-*agent*: nothing chooses the next specialist, routing is invisible, and the README “orquestador” is missing. Course S14 and Cristian use a star hub; we need that topology (with Metropol names), plus a visible domain tag and a configure/catalog surface for the entrega.

## What Changes

- Re-wire the agentic graph to a **star**: `orchestrator` hub ↔ pipeline specialists, then `escalation_gate`
- Deterministic legal ladder + `AGENTIC_ORCHESTRATOR_MAX_STEPS`; record `routing_history`
- Metropol **domain** tag (`ventas|cobranzas|operacion|tenela|general`): auto-detect + optional request/UI override; light prompt/retrieve bias
- Server **agent catalog** (`GET /api/v1/answer/agents`) as single source of truth
- Frontend `/answer`: show domain chip + orchestrator routes in progress/trace; domain select
- Frontend `/agents` (Astryx, SideNav): catalog + flow summary + knobs (read max steps / threshold from API or documented env)
- Docs in `AGENTS.md`

## Capabilities

### New Capabilities
- `agentic-orchestrator`: Star-topology hub, routing history, step budget, agent catalog endpoint, Metropol domain tagging for agentic runs

### Modified Capabilities
- `agentic-answer`: Graph shape and state include orchestrator routing + domain; specialists unchanged in role
- `agentic-live-progress`: Progress/activity narrates orchestrator decisions and domain when present
- `agentic-chat-ui`: Domain control + routing visibility on `/answer`; new `/agents` console for catalog/config

## Non-goals

- LLM supervisor that picks the next agent (full course S14)
- Separate LLM nodes per business domain (Ventas/Cobranzas as agents)
- Re-query loops in v1
- Multi-model profiles in DB
- Auth; replacing sync `POST /answer`

## Impact

- **backend:** `domain/graph/{build,orchestrator,catalog,state,activity,gate}`, schemas, config, routes, tests
- **frontend:** `answer/page`, `app-shell` nav, new `app/agents`, API client for catalog
- **Graphify notes:** extend hubs `build_agentic_answer_graph`, `AgenticAnswerRunner`, `GraphActivityLog`, `answer/page.tsx` — no parallel island outside `domain/graph/`

## Practices check

- **Aligned:** graph logic in `domain/`; thin routers; settings via `config.py`; Astryx on front
- **Deviations:** deterministic ladder vs course LLM supervisor (peer-aligned); domain as tag not domain-LLM agents
- **Risks if ignored:** hub without step budget → loops; catalog only in UI → drift; “multiagent” as cosmetic labels only
