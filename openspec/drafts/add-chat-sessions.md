# Draft: add-chat-sessions

## Surface
- Primary: **both**
- Backend: session CRUD + durable transcript (Postgres); wire agentic completed/resumed turns into `history`
- Frontend: `/answer` — varias sesiones, listado, nueva chat, reopen via `?session=`; Astryx `ai-chat` (Toolbar / lista / ChatLayout), **no** layout a mano
- Course reference: `session_16` `generation/conversation/` — Session + in-process `SessionStore` (forma); peer lidr-master → Postgres `conversation_sessions` + `POST/GET/PATCH/DELETE /answer/session*` (persistencia real)
- Patterns borrowed (not copied):
  - `session_id` ≠ `thread_id` (session spans many graph runs; thread = one run)
  - Service mints `session_id`; client never invents ids
  - List on sibling route `/answer/sessions` so `sessions` is not captured as `{session_id}`
  - Transcript `history[]` for UI reopen; optional memory window later
  - Astryx `ai-chat` frame for sidebar/session chrome on existing `/answer`

## Intent
Permitir **varias conversaciones en paralelo**: crear, listar, abrir, renombrar y borrar sesiones; al F5/reabrir, restaurar el transcript desde el backend (no solo estado React). Cada envío sigue siendo un run agentic con su `thread_id`; la sesión agrupa turnos.

## Graphify notes
- Queried: `agentic chat session history transcript thread_id answer page`
- Hubs: `answer/page.tsx`, `agentic.ts`, `AgenticAnswerRunner`, routes `answer_agentic`, persistence stack
- Extender `/answer` + API agentic; nuevo módulo `generation/conversation/` o `domain/sessions/` + router fino — no meter transcript en el checkpointer LangGraph
- Gaps: hoy no hay sesión ni history API; UI es single-thread en memoria

## Non-goals (v1)
- Memoria RAG cross-turn completa (facts / anchors / `resolved_question` en el prompt) — follow-up; v1 = **transcript durable + UI multi-sesión**
- Auth / multi-tenant owner (peer `owner_id`); v1 single-tenant local
- Persistir activity log de live progress
- Orchestrator / supervisor
- Scaffold nueva ruta `frontend/src/app/ai-chat` — evolucionar `frontend/app/answer/` con patrones del template

## Draft requirements
- API:
  - `POST /api/v1/answer/session` → 201 + `session_id`
  - `GET /api/v1/answer/sessions` → lista (`session_id`, title, timestamps, turn_count)
  - `GET /api/v1/answer/session/{id}` → `SessionView` con `history[]` (question, answer, citations snapshot, status/thread refs útiles)
  - `PATCH` rename title; `DELETE` 204
- Persistencia: tabla Postgres (Alembic); JSON history o filas de turns — preferir modelo simple peer-like (`history` JSONB) salvo que practices digan lo contrario
- Agentic: `start` (y sync si aplica) acepta `session_id` opcional; al terminal **completed** (y tras resume exitoso) append del turno a esa sesión; sin `session_id` el comportamiento actual se mantiene
- Front (Astryx `ai-chat`):
  - Lista de sesiones (varias a la vez) + “Nueva chat”
  - URL `?session=<id>` restaura historial al cargar
  - Mensajes previos del `history` en el hilo; nuevo envío usa el `session_id` activo
  - Gate humano / progress siguen igual por `thread_id`
- Docs: `AGENTS.md` + `frontend/AGENTS.md` (session vs thread)

## Approach sketch
```text
backend/
  foundation/persistence + alembic → conversation_sessions
  generation/conversation/store.py (or domain/sessions/) → SessionStore
  api/routes/answer_session.py → CRUD
  agentic start/resume → append history on terminal success

frontend/app/answer/
  extend page with session list (ai-chat Toolbar/List patterns)
  lib/api/sessions.ts + agentic.ts session_id
  ?session= deep link
```

**v1 vs Cristian:** mismo modelo sesión/transcript/listado; diferimos memoria de generación (facts/anchors) y auth a un change posterior.

## Practices check (backend)
- Aligned: router fino; store en foundation/generation; schemas Pydantic; Alembic; no SQL en routes; deps en composition root.
- Deviations: sin owner/auth (single-tenant demo); history JSONB vs tabla normalizada (simpler v1, peer-aligned).
- Risks if ignored: confundir session con thread/checkpointer; inventar session_id en el cliente; UI solo localStorage sin API.

## Impact
- backend: models, migration, session store/routes, agentic wiring, tests
- frontend: `/answer` multi-sesión + API client; Astryx components only

## Open questions
- ¿Append también turnos `rejected`? **Propuesta:** sí, con flag/`status` en el turn para que el historial sea auditable.
- ¿Título auto desde primera pregunta? **Propuesta:** sí (truncate); renombrable con PATCH.
- ¿Memoria en el LLM en el mismo change? **Propuesta:** no — solo transcript UI + storage.

## Status
- [x] User approved — ready for OpenSpec propose
