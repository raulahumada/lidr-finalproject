# Draft: add-session-memory

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/domain/graph/` (state, intent_framer, corpus_fetcher, grounded_composer, runner), `backend/app/generation/conversation/`, `backend/app/foundation/prompts/answer/`, `config.py`
- Frontend: **ninguno en v1** — ya manda `session_id`; transcript UI ya existe
- **Course reference** (`session_16` / `ai-service`): `generation/conversation/` — sliding window + summary/anchors; el conductor mete history en **generación** (`messages.extend(session.history.to_messages())`). Dominio estimador, no RAG Q&A.
- **Peer Cristian** (`.reference/lidr-master/`): capability `conversation-memory` — memoria alimenta **RECUPERACIÓN primero**, generación después. Módulos: `facts`, `resolver` (`resolved_question`), `anchors`, `budget` (`render_memory`), `store`. Spec: `openspec/specs/conversation-memory/`. Diff estructural vs curso documentado en su `__init__.py` / proposal archive `2026-09-10-add-conversation-memory`.

## Architecture check (curso × Cristian × Metropol)

| Pieza | Curso (estimador) | Cristian (RAG seguros) | Metropol v1 (propuesta) |
|-------|-------------------|------------------------|-------------------------|
| Problema | Modelo olvida compromisos en chat | Follow-up roto llega al **retriever** → respuesta citada a la pregunta equivocada | Igual que Cristian (corpus Metropol + agentic RAG) |
| Dónde actúa la memoria | Sobre todo en **generación** | **Resolver antes de retrieve** + bloque memoria en síntesis (detrás de evidencia) | Igual que Cristian: resolve → `framed_query` / `resolved_question` → retrieve; window en composer |
| Sesión vs thread | Session in-process | `session_id` ≠ `thread_id`; sync `/answer` **422** si manda session | Ya tenemos sessions Postgres; agentic opcional `session_id`; sync sin memoria (no aceptar engañoso) |
| Rewrite | N/A (multi-turn messages) | Resolver **determinista y conservador** (sin LLM); visible `substituted` | **Portar forma** del resolver (heurística ES + hechos mínimos), no LLM rewrite |
| Window | max_turns + summary + anchors | `CONVERSATION_MAX_TURNS=4` + budget tokens; evidence wins | Window N=4 + tope tokens; evidence wins |
| Facts / anchors | ProjectMetadata / NDA-style | Facts + anchors de dominio (filtros, txs) | **Defer** facts/anchors ricos; v1: últimos turnos + resolve con referents del turno previo (question/answer/citas) |
| Nombres | Estimador | `query_planner`, `evidence_retriever`, … | Mantener **nombres Metropol** (`intent_framer`, `corpus_fetcher`, `grounded_composer`) |

**Regla de trabajo (este draft y siguientes):** siempre contrastar `.reference/ai-engineering` (curso) **y** `.reference/lidr-master` (Cristian) antes de cerrar approach; no inventar memoria solo desde el monorepo local.

## Intent
Que follow-ups (“¿y con Tenela?”, “¿eso también aplica a cobranzas?”) se **resuelvan antes del retrieve** y el composer vea una ventana corta de turnos, sin tratar el history como evidencia citable.

## Graphify notes
- Queried: `conversation session memory history resolved_question prompt composer retrieve`
- Hubs: `SessionStore`, `AgenticAnswerRunner`, `intent_framer`, `grounded_composer`, `corpus_fetcher`
- `path SessionStore → grounded_composer`: **sin path dirigido** — gap real (store append-only)
- Extender `generation/conversation/` (peer-shaped) + cablear en `intent_framer` / composer; no isla nueva fuera de capas

## Non-goals (v1)
- Facts store completo + anchors de dominio (peer slice completo) — follow-up
- Compression LLM / rolling summary del curso
- Auth / ownership / TTL de sesión (peer tiene TTL; nosotros documentar follow-up)
- Orquestador
- UI nueva
- Meter `session_id` en sync `POST /answer` fingiendo memoria (peer: 422; nosotros: **no aceptar o ignorar documentado** — propuesta: dejar sync sin campo / rechazar si aparece)

## Draft requirements
- Con `session_id` en agentic start/sync: hidratar ventana de últimos **N=4** turnos cerrados desde `SessionStore`
- **Antes de retrieve**, resolver pregunta referencial → `resolved_question` / `framed_query` (conservador: si ya nombra sujeto o no hay referente, no reescribir). Exponer en state/trace (y opcionalmente response) si hubo rewrite + `substituted`
- `corpus_fetcher` busca con la pregunta resuelta
- `grounded_composer`: bloque “memoria / historial reciente” en prompt, **subordinado al presupuesto de evidencia** (evidence wins; trim turnos primero)
- History **no** es fuente de citas
- Sin `session_id`: comportamiento byte-compatible con hoy
- Tests: follow-up referencial reescribe; pregunta autosuficiente no; sin session no regresa; budget no ahoga evidencia

## Approach sketch
```text
generation/conversation/   # peer-shaped, Metropol names
  store.py                 # ya existe (transcript)
  resolver.py              # NEW — forma Cristian, referents desde último turno / window
  budget.py                # NEW — render_memory + trim (tokens)
  # facts.py / anchors.py  # OUT of v1

domain/graph/
  state: + conversation_window, resolved_question (framed_query = resolved)
  runner: hydrate window from SessionStore when session_id
  intent_framer: call resolver (deja de ser solo pass-through)
  corpus_fetcher: framed_query (ya)
  grounded_composer: inject render_memory(...) behind evidence budget

prompts/answer: bloque opcional historial (no inventar citas desde ahí)
```

## Practices check (backend | both only)
- Aligned: lógica en `generation/conversation` + graph nodes; runner conductor hidrata; routers finos; settings para N / memory token budget; tests unitarios del resolver
- Deviations (+ why): sin facts/anchors peer en v1 (slice mínimo usable); sync path sin memoria (igual peer: no fingir)
- Risks if ignored: LLM rewrite agresivo → retrieve confiado y equivocado (peer lo evita a propósito); memory sin budget → desplaza evidencia

## Impact
- backend: conversation helpers + intent_framer + state/runner + prompts + tests + AGENTS.md (memoria ≠ transcript ≠ checkpointer)
- frontend: ninguno en v1

## Open questions
- ¿Rechazar `session_id` en sync `POST /answer` con 422 (peer) o simplemente no documentar el campo? **Propuesta: 422 si llega**, para no mentir
- ¿Persistir `resolved_question` en cada turn del JSONB history? **Propuesta: sí** (útil UI/debug; peer lo guarda en Turn)
- ¿Settings `CONVERSATION_MAX_TURNS=4` y `CONVERSATION_MEMORY_MAX_TOKENS≈1024` como peer? **Propuesta: sí**

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-session-memory`
