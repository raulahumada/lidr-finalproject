# Draft: add-ai-model-settings

## Surface
- Primary: **both**
- Paths in this repo:
  - backend: `app/foundation/llm/runtime_config.py` (nuevo), `app/api/routes/config_models.py` (o `config.py`), `app/schemas/config_models.py`, `dependencies.py`, `ChatClient` / composition root para resolver modelo efectivo; `config.py` + `.env.example` (`AVAILABLE_CHAT_MODELS`)
  - frontend: `app/settings/page.tsx` (stub hoy), `lib/api/config.ts`, SideNav ya apunta a `/settings`
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/` @ `d2f015f`
  - `foundation/llm/runtime_config.py` — overrides Redis; `.env` = defaults
  - `api/config.py` — `GET/PUT /models`; embedding **no** overrideable
- Peer Cristian: `/models` + catálogo multi-proveedor / keys write-only — **más grande**; nosotros tomamos la idea de “cambiar chat model en caliente”, no el marketplace de providers
- Patterns borrowed (not copied):
  - Settings defaults inmutables; runtime = deltas en Redis
  - Read soft-fail → default `.env`; write fail → 503
  - Allowlist de modelos disponibles
  - Embedding fuera del hot-swap (rompe el índice)

## Intent
Permitir al operador elegir **modelos de chat por rol** (router simple) desde la consola `/settings`, sin editar `.env` ni reiniciar Uvicorn — paridad demo con Cris/curso en lo esencial (hot models), sin el CRUD completo de proveedores.

## Graphify notes
- Queried: `chat_model embedding_model ChatClient runtime config models settings`
- Hubs: `Settings` / `get_settings`, `ChatClient`, `dependencies.get_answer_service` / `get_agentic_answer_runner`, `AgenticAnswerRunner`, `AnswerService`
- Gap: no hay `runtime_config` ni rutas `/config/models`; `ChatClient.model` se fija al construir el cliente
- Prefer extend: `foundation/llm/` + thin `api` route; frontend `/settings` ya en SideNav

## Non-goals
- Multi-proveedor (Anthropic/Azure) o almacenamiento de API keys en UI (sigue `OPENAI_API_KEY` en `.env`)
- Override de **embedding** model por HTTP (invalidaría pgvector)
- LiteLLM / Instructor del curso
- Auth (siguiente change del lote)
- Cambiar prompts / temperature / knobs agentic desde esta pantalla
- Persistencia en Postgres (Redis basta; ya está en Compose)

## Draft requirements
### Backend — runtime model config + router
- Store Redis (hash) de overrides, p. ej. `lidr:runtime_models`, keys = roles:
  - `chat` — path sync `POST /answer` y default agentic
  - `composer` — `grounded_composer`
  - `prompt_specialist` — customs / `prompt_specialist`
  - (opcional v1: si un rol no tiene override, cae a `chat` → `settings.chat_model`)
- `GET /api/v1/config/models` → por rol: `{ effective, default, overridden }` + `available_models` (allowlist) + nota de que embedding es `.env`-only
- `PUT /api/v1/config/models` body `{ "models": { "chat": "gpt-4o-mini", "composer": null, … } }` — `null` limpia override; valor fuera de allowlist → **422**; Redis down en write → **503**
- Allowlist desde settings: `AVAILABLE_CHAT_MODELS` (CSV; default razonable: `gpt-4o-mini,gpt-4o`)
- `ChatClient` (o wrapper) resuelve el modelo **por llamada** vía runtime config + rol, no solo el string congelado en `__init__`
- Composition: runners/services reciben runtime config (o factory); sin lógica de Redis en el router más allá de get/put
- Tests: effective fallback; put/get roundtrip con fake redis o skip si no hay; 422 unknown model; embedding no aparece como key mutable

### Frontend — `/settings`
- Reemplazar stub de `/settings` con form Astryx: selectores por rol (chat / composer / specialist) + “usar default” + save
- Cliente `lib/api/config.ts`; estados loading / 503 Redis / success
- Docs smoke en `frontend/AGENTS.md`; `tsc --noEmit`
- SideNav **Ajustes** ya existe — no hace falta entrada nueva

## Approach sketch
1. Portar forma del curso `RuntimeModelConfig` simplificada (3 roles Metropol, no 9 knobs del estimador).
2. Thin router bajo `/api/v1/config/models`.
3. Thread effective model into `ChatClient.complete_json(..., model=?)` o property `effective_model(role)`.
4. Wire agentic composer + prompt_specialist + sync answer to roles.
5. UI `/settings` Astryx (Switch/Select + Button save).

## Practices check (backend | both only)
- Aligned: settings defaults vía `get_settings()`; secrets siguen en env; router fino; foundation/llm para runtime store; schemas Pydantic; Redis ya en stack
- Deviations: allowlist CSV simple vs catálogo providers del peer — **por qué:** un solo OpenAI key local; multi-provider es otro change. Roles Metropol ≠ PRIMARY/FALLBACK/CRITIC del estimador — **por qué:** dominio distinto, mismos 1–2 modelos de chat
- Risks if ignored: modelo hardcodeado en cliente cacheado → PUT no tiene efecto; permitir embed override → embeddings viejos; keys en UI sin auth

## Impact
- backend: runtime_config, config routes/schemas, ChatClient/deps, tests, `.env.example`, `AGENTS.md`
- frontend: `/settings` real + API client + docs
- openspec: capability nueva `ai-model-settings` (+ UI `ai-settings-console` o un solo capability — **propuesta: `runtime-model-config` + `ai-settings-ui`**)

## Open questions
- ¿Tres roles (`chat`/`composer`/`prompt_specialist`) o un solo `chat_model` global en v1? → **Default: tres roles con fallback a `chat`** (multi-router mínimo demo).
- ¿Allowlist solo env o también hardcode defaults en código? → **Default: env CSV + defaults en Settings**.
- ¿Mostrar embedding como read-only en UI? → **Default: sí**, texto informativo.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-ai-model-settings`
- Applied (HTTP + `/settings` + tests + smoke)
- Synced to main specs + archived → `openspec/changes/archive/2026-10-13-add-ai-model-settings/`
- Logged in `openspec/history.md`
