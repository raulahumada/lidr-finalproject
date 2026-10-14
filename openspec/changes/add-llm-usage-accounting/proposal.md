# Proposal

## Why

Cada completion de chat se paga, pero `ChatClient.complete_json` descarta `response.usage`. Solo existen estimaciones de presupuesto (tiktoken) en el path RAG; el operador no puede auditar tokens por modelo, sesión o purpose sin el dashboard de OpenAI. Tras dual-auth y ownership, la consola ya es el lugar natural para un ledger de uso admin-only.

## What Changes

- Extraer usage reportado por el proveedor en cada `complete_json` exitoso (`input_tokens` / `output_tokens` / `total_tokens` / `reported`).
- Persistir una fila en Postgres (`llm_usage_events`) **en el momento de la llamada** en los paths HTTP de answer (sync + agentic specialists).
- Incluir `usage` (última completion) en `AnswerResponse` y en payloads agentic completed / paused / progress.
- Nuevo `GET /api/v1/usage/summary` con totales y `by_model`, filtros `from` / `to` / `session_id` / `purpose`.
- Consola admin `/usage` (Astryx) + BFF + gates `administrador`.
- **No BREAKING** de contrato previo: campos nuevos opcionales/additive; clientes viejos ignoran `usage`.

## Non-goals

- Costo en USD / tablas de tarifas / cache-token pricing.
- Tokens de embeddings / ingest.
- Asientos desde el eval harness cuando usa doubles pelados.
- Mezclar usage en el transcript de sesión (`HistoryTurn`).
- Streaming o adaptadores Anthropic.
- Multi-tenant `TENANT_ID` (deploy single-tenant Metropol).
- Agregado `by_purpose` en el summary (el filtro `purpose` alcanza).

## Decisions (from draft open questions)

1. **Sí** persistir `owner_id` nullable cuando el BFF manda `X-Console-User`.
2. Hits CAG / no LLM: `usage` en ceros + `reported=false`; el flag `cached` sync ya existe — no se añade otro.
3. Summary: `by_model` only; sin `by_purpose`.

## Capabilities

### New Capabilities

- `llm-usage-accounting`: provider-reported token usage on chat completions, durable ledger rows, HTTP `usage` on answer payloads, and `GET /usage/summary`.
- `usage-console-ui`: admin console screen and BFF to inspect ledger aggregates.

### Modified Capabilities

- `rag-answer`: sync answer response SHALL include last-completion `usage`.
- `agentic-answer`: completed / paused / rejected payloads SHALL include last-completion `usage`.
- `agentic-live-progress`: progress payloads SHALL include last-completion `usage` when known (zeros while no model call yet).
- `console-authentication`: admin-only path `/usage` and upstream `/api/v1/usage` gated to `administrador`.

## Impact

- **Surface:** both (`backend/` + `frontend/`).
- **Backend:** `foundation/llm/chat.py`, new persistence model/store + Alembic, `dependencies.py` wiring, `AnswerService` / `grounded_composer` / `prompt_specialist`, answer + agentic schemas/routes, new `routes/usage.py`.
- **Frontend:** `/usage` page (Astryx), BFF route, `roles.ts` (`ADMIN_ONLY` + `isAdminUpstreamPath`), types.
- **Infra:** Postgres migration on Railway; no new paid deps beyond existing OpenAI SDK fields.

### Graphify notes

- Hubs: `ChatClient`, `AnswerService`, `AgenticAnswerRunner`, `dependencies.py`, `persistence/models.py`.
- Call sites of `complete_json`: sync answer, `grounded_composer`, `prompt_specialist`.
- No existing usage-ledger node — new island under `foundation/persistence` + thin API route; prefer extending `ChatClient` over a parallel wrapper.

## Practices check

- **Aligned:** thin routers; schemas in `app/schemas/`; composition in `dependencies.py`; Alembic for table; store under `foundation/persistence`; fail-open ledger vs answer path; no LLM logic in the usage router.
- **Deviations:** optional `owner_id` on events (peer Cristian omitted `user_id` without auth; we have trusted BFF header). Single-tenant summary without `TENANT_ID`.
- **Risks if ignored:** inventing tokens → false spend; failing answers on ledger outage → availability; shipping USD in v1 → stale tariffs; hanging embeddings on this ledger → muddied purposes.
