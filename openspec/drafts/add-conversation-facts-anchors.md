# Draft: add-conversation-facts-anchors

## Surface
- Primary: **backend**
- Paths: `backend/app/generation/conversation/` (`facts.py`, `anchors.py`, models), wire in `intent_framer` / runner / `render_memory` / session store; tests; `AGENTS.md`
- Course reference (`session_16`): conversation commitments (NDA/scope) vía LLM extract — **forma** (durable pins), no vocabulario estimador
- Peer Cristian (`.reference/lidr-master`): `facts.py` + `anchors.py` + `models.py` — facts **derivados del turno** (sin 2º LLM); anchors por **heurística de scoping** (“de acá en adelante…”); feed **retrieve first**

## Intent
Completar el slice de memoria que deferimos en `add-session-memory`: **facts** de sesión (dominio Metropol, docs citados, códigos/entidades) y **anchors** de alcance que el usuario fija a propósito, para que follow-ups no dependan solo de la ventana corta de turnos.

## Graphify notes
- Queried: `conversation memory facts anchors resolver budget`
- Hubs: `resolve`, `render_memory`, `SessionStore`, `intent_framer`, archive design “no facts store yet”
- Gaps: no existen `facts.py`/`anchors.py` locales — extender el paquete peer-shaped ya presente

## Non-goals
- 2º LLM para extraer facts (peer los deriva del pipeline)
- Auth / ownership / TTL
- Cambiar UI (salvo exponer anchors/facts en response más adelante)
- Business-DB / Visual Time filters del peer
- Multiturn eval (change aparte)

## Draft requirements
- Modelo `ConversationFacts` + `Anchor` (Metropol: p. ej. domain tag, document_ids citados, entidades Tenela/cobranzas detectadas sin inventar filtros que vacíen el retrieve)
- `facts_from_turn(...)` merge en sesión (persistir en session row o JSONB session meta — **default: campo en session / history side-channel**, sin Alembic si cabe en JSONB existente; si no, migración mínima)
- `detect_anchors(question)` heurístico ES (“de acá en adelante”, “solo cobranzas”, “quedate en Tenela”); **conservador** (falso positivo ensancha/acota mal → preferir miss)
- Anchors + facts entran al **resolver / retrieve bias** y al bloque `render_memory` (evidence wins en budget)
- Sin session_id: no-op
- Tests unitarios facts merge + anchors detect + “no pin silencioso que vacía retrieve”
- Docs en `AGENTS.md` (memoria = window + facts + anchors)

## Approach sketch
```text
generation/conversation/
  models.py      # NEW
  facts.py       # NEW — peer-shaped, Metropol entities
  anchors.py     # NEW — ES scoping phrases → domain/corpus pins
  resolver.py    # use facts/anchors as referents
  budget.py      # render facts/anchors in memory block
  store.py       # persist session facts/anchors JSON
domain/graph: intent_framer + runner hydrate/merge after turn
```

## Practices check (backend | both only)
- Aligned: lógica en `generation/conversation`; graph conductor; tests offline; settings si hace falta tope de facts
- Deviations: vocabulario Metropol ≠ peer Visual Time — consciente
- Risks if ignored: anchor falso → retrieve vacío silencioso (peer lo documenta); facts LLM → costo/falla

## Impact
- backend: conversation + graph hydrate + tests + docs
- frontend: none (v1)

## Open questions
- ¿Persistir facts en `conversation_sessions` JSONB column nueva vs embeber en history? → **Default: columna/meta JSON en session** (Alembic si el modelo no tiene bag).
- ¿Anchor de domain overridea el Selector UI? → **Default: sí para retrieve bias en esa sesión**, UI selector sigue ganando en el request actual si se envía.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change 
- Promoted to openspec change `add-conversation-facts-anchors`
