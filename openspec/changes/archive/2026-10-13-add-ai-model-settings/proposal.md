# Proposal: add-ai-model-settings

## Why

Chat models are fixed in `.env` (`chat_model`) and baked into `ChatClient` at composition time. Operators (and demos vs Cristian’s `/models`) cannot hot-swap models or route different roles to different chat models without restart. Closing that gap with a course-shaped Redis override store keeps Metropol demos flexible without a full multi-provider catalog.

## What Changes

- Redis-backed runtime overrides for chat roles: `chat`, `composer`, `prompt_specialist` (fallback chain to `chat` → settings default)
- `GET/PUT /api/v1/config/models` with allowlist validation; embedding model exposed read-only only
- `ChatClient` / runners resolve effective model per call (or per role), so PUT takes effect without reload
- Replace `/settings` stub with Astryx model selectors + save
- No **BREAKING** API removals (additive config surface)

## Non-goals

- Multi-provider / API-key management in UI
- HTTP override of embedding model
- Auth, LiteLLM, prompt/temperature knobs, Postgres-backed config

## Capabilities

### New Capabilities

- `runtime-model-config`: Redis overrides + HTTP get/put for chat-role models and allowlist
- `ai-settings-ui`: operator console at `/settings` to view/edit those overrides

### Modified Capabilities

None (behavior of answer/agentic stays the same contract; only which OpenAI chat model string is used).

## Impact

- **Surface:** both
- **Backend:** `foundation/llm/runtime_config.py`, config routes/schemas, `ChatClient` + dependencies/runners, `.env.example`, tests, `AGENTS.md`
- **Frontend:** `/settings`, `lib/api/config.ts`, `frontend/AGENTS.md`
- **Infra:** existing Redis Stack (same as Response CAG)
- **Course ref:** `runtime_config` + `GET/PUT /models` shape from `session_16` (simplified roles)

### Graphify notes

- Hubs: `ChatClient`, `get_answer_service` / `get_agentic_answer_runner`, `Settings`, Redis already in `dependencies`
- Gap: no runtime override path today — extend `foundation/llm/` rather than a parallel config island

## Practices check

- **Aligned:** thin API router; settings defaults via `get_settings()`; secrets stay in env; foundation store for Redis overrides; Pydantic schemas
- **Deviations:** CSV allowlist vs peer provider catalog — single OpenAI key local; Metropol roles vs estimator PRIMARY/FALLBACK/CRITIC — domain fit
- **Risks if ignored:** cached fixed `ChatClient.model` ignores PUT; embed override would stale vectors; open PUT without auth (deferred to next change)
