# Draft: show-custom-agent-notes

## Surface
- Primary: **both**
- Backend: exponer `custom_notes` en payloads agentic (sync/progress/resume); schemas + runner; tests
- Frontend: `/answer` muestra notas de customs (live + terminal) junto a ruteo/trace; tipos en `agentic.ts`; docs
- Course reference (`session_16`): activity/trace visible al operador; no inventar UI Streamlit
- Peer Cristian: “se ve qué aportó cada agente” en la corrida — mismo objetivo, datos Metropol
- Patterns: extender schemas/runner existentes; Astryx en chat (List / Banner / ChatToolCalls), sin JSON crudo

## Intent
Hoy el custom (`prompt_specialist`) escribe `custom_notes` en el state y el composer las usa por debajo, pero la API/UI **no las muestran**. El operador crea `risk_advisor` y no ve su aporte en el chat. Este change cierra el loop demo: crear custom → corrida → nota visible.

## Graphify notes
- Queried: `custom_notes prompt_specialist agentic progress chat answer page`
- Hubs: `prompt_specialist`, `AgenticAnswerRunner` / `_to_response`, `answer_agentic_progress`, `agentic.ts`, `AnswerPageInner`
- Gap: `custom_notes` solo en state + composer; no en schemas/API/front

## Non-goals
- Editar notas a mano; re-ejecutar solo el custom
- Cambiar el ladder o el contrato de citas
- Persistir `custom_notes` en el transcript de sesión (follow-up opcional)
- Personas/prompts en builtins

## Draft requirements
- Payloads agentic completed / paused / rejected / progress SHALL include `custom_notes: [{key, note}, …]` (lista, default vacía)
- Mientras `running`, progress MAY incluir notas ya acumuladas (si el nodo custom ya corrió)
- UI `/answer`: sección visible “Aportes de agentes custom” (o equivalente) cuando hay notas; key + texto; Astryx
- Live: actualizar cuando progress trae `custom_notes`
- Docs cortas en `frontend/AGENTS.md` (+ mención en root `AGENTS.md` si hace falta)
- Tests: runner/API incluyen notas cuando el state las tiene; typecheck front

## Approach sketch
```text
backend:
  schemas/agentic_answer.py   # CustomAgentNote + field on response/progress
  domain/graph/runner.py      # map state["custom_notes"] → payload
  tests                      # progress/response shape

frontend:
  lib/api/agentic.ts         # type + progressToAnswer
  app/answer/page.tsx        # List/Banner de notas (live + terminal)
  AGENTS.md
```

## Practices check (backend | both only)
- Aligned: schema Pydantic tipado; runner mapea state→DTO; sin lógica nueva en router
- Deviations: none
- Risks: notas largas → truncar en UI (no en API) o max length en schema opcional

## Impact
- backend: schemas, runner, tests
- frontend: agentic client + `/answer` surface

## Open questions (defaults)
- ¿Append a history de sesión? → **Sí** (persistido en el turn al completar/rechazar).
- ¿Mostrar también el summary de `agent_trace` del specialist? → **Default: campo `custom_notes` es la fuente**; trace sigue como hoy.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `show-custom-agent-notes`
- Synced to main specs + archived `2026-10-13-show-custom-agent-notes`

