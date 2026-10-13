# Design

## Context

See proposal.md — Why. Today `Settings.chat_model` seeds a `ChatClient` once in `dependencies` (Graphify hubs: `ChatClient`, `get_answer_service`, `get_agentic_answer_runner`). Redis already exists for Response CAG. Course `RuntimeModelConfig` is the pattern; Cris `/models` is multi-provider (out of scope). Frontend `/settings` is a placeholder; SideNav already links there.

## Goals / Non-Goals

**Goals:**
- Hot-swap chat models per role without restart
- Minimal multi-router: three roles with fallback
- Operator UI on existing `/settings` route

**Non-Goals (design-level):**
- Provider abstraction / key vault
- Changing embedding or reindexing
- Per-request model from the chat UI (only global runtime overrides)

## Decisions

1. **Redis hash `lidr:runtime_models` for overrides**  
   Same failure semantics as course: read miss/Redis down → settings default; write fail → 503.  
   *Alt:* Postgres table — deferred; Redis already required for local answer path.

2. **Roles: `chat` | `composer` | `prompt_specialist`**  
   Effective resolution: role override → `chat` override → `settings.chat_model`.  
   *Alt:* single global override only — weaker demo of “multi-router”; rejected for v1 defaults in draft.

3. **Embedding is read-only in GET payload** (`embedding_model` + note); never a PUT key.  
   *Alt:* allow embed swap — rejected (invalidates pgvector).

4. **Allowlist `AVAILABLE_CHAT_MODELS` CSV on Settings**  
   PUT validates membership → 422. Defaults include `gpt-4o-mini,gpt-4o`.  
   *Alt:* free-form any string — unsafe typos / cost surprises.

5. **Resolve model at call time**  
   Extend `ChatClient.complete_json` to accept optional `model=` or hold a callable/resolver for role; wire composer → `composer`, prompt_specialist → `prompt_specialist`, sync answer → `chat`.  
   *Alt:* rebuild service singletons on PUT — harder with `@lru_cache` deps; rejected.

6. **Thin router `GET/PUT /api/v1/config/models`**  
   Schemas in `schemas/`; store in `foundation/llm/runtime_config.py`. No Redis imports in domain agents beyond injected config.

7. **Frontend:** replace stub; Select per role + clear-to-default + Save; show embedding as Text. Reuse SideNav Ajustes.

## Layer map

| Piece | Layer |
|-------|--------|
| `config.py` allowlist field | config |
| `foundation/llm/runtime_config.py` | foundation |
| `schemas/config_models.py` | schemas |
| `api/routes/config_models.py` | api |
| `ChatClient` role-aware complete | foundation/llm |
| `dependencies` wiring | composition root |
| Agents/runner pass role | domain/generation (call sites only) |

**Tension:** agents must not import Redis; they receive effective model via ChatClient API or a small protocol injected at composition.

## Risks / Trade-offs

- [PUT without auth] → Mitigation: localhost demo; auth is next planned change
- [Redis down: writes 503, reads degrade] → Document; answer path keeps working on defaults
- [Exact answer CAG keyed without model] → Trade-off: changing model may serve stale cached answers until TTL; note in AGENTS.md; flush Redis optional for demos
- [Allowlist drift vs OpenAI catalog] → Operator updates env CSV

## Migration Plan

1. Deploy backend + ensure Redis up
2. Ship `/settings` UI
3. Rollback: remove routes/UI; `.env` chat_model still works

## Open Questions

None (draft defaults locked).
