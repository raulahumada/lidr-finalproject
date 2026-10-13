# Draft: add-agentic-chat-ui

## Surface
- Primary: **frontend**
- Paths in this repo: `frontend/app/answer/` (upgrade E1), `frontend/app/lib/api/` (cliente agentic), shell nav existente; docs `frontend/AGENTS.md`
- Reuse backend (sin reimplementar): `POST /api/v1/answer/agentic`, `POST /api/v1/answer/agentic/{thread_id}/resume`, schemas en `backend/app/schemas/agentic_answer.py`
- Course reference: `session_16` / `ai-service` — UI = cliente HTTP mínimo (`streamlit_app.py` → form → API); forma útil = pantalla que llama API y renderiza resultado, no Streamlit
- Peer reference (patrón, no copiar shadcn/BFF verbatim): `lidr-master/business-backend` consola answer agentic (202 ≠ error; gate humano approve/reject/adjust; traza)
- Patterns borrowed (not copied):
  - Tratar **HTTP 202** como pausa deliberada, no fallo
  - UI de revisión humana + `agent_trace` + citas
  - **No** copiar `/start` + progress polling (nuestra API v1 no lo expone)
  - Astryx `ai-chat` (+ `Citation`) en lugar de shadcn del peer
  - Dominio Metropol Fintech

## Intent
**E2** del roadmap de UI: chat agentic sobre el grafo LangGraph ya mergeado — pregunta → corrida con traza → si hace falta, gate humano (approve / reject / adjust) → respuesta + citas. Scaffold desde template Astryx **`ai-chat`** (confirmado con `astryx build`).

## Graphify notes
- Queried: `agentic answer frontend chat UI resume thread`; `graphify explain "agentic answer"`; path front↔agentic → sin edge dirigida (esperado: UI aún no cableada)
- Hubs / communities:
  - Backend: `AgenticAnswerRunner` (`runner.start` / `.resume`), `answer_agentic` / `resume_agentic`, schemas `AgenticAnswerResponse` / `AgenticResumeRequest`, community `AgenticAnswerRunner`
  - Front existente: `layout.tsx` / `AppShellLayout`, `app/answer/page.tsx`, `lib/api/answer.ts` (solo sync)
- Relevant edges: API agentic ya completa; front sync no toca agentic — este change crea el puente cliente
- Gaps: ningún nodo de UI agentic en el grafo (esperado). Tras apply: `graphify update .`

## Non-goals
- Backend nuevo: `/start`, progress polling, orchestrator hub, Postgres checkpointer
- Cambiar contratos agentic salvo docs/claridad de consumo front
- Auth, BFF Next proxy (seguir fetch directo a FastAPI como E1)
- Multi-turno con memoria de conversación (cada submit = una corrida agentic)
- Reemplazar o romper el path sync `POST /answer` en API; en UI, sync puede quedar como toggle secundario o ruta legacy mínima
- Inventar layout con `<div>` / CSS a mano; Streamlit

## Draft requirements
- Scaffold Astryx: `npx astryx template ai-chat ./app/answer` (o path acordado; `--overwrite` si se reemplaza E1). Instalar `@heroicons/react` si el scaffold lo pide. Mantener frame/gap del template; reemplazar contenido demo.
- Ruta `/answer` (o subruta clara) accesible desde SideNav existente; copy/nav puede pasar a “agentic” o toggle Sync | Agentic.
- Cliente thin tipado: `postAgenticAnswer` + `resumeAgenticAnswer` (reusar `getApiBaseUrl` / errores 503/network de E1).
  - `POST …/answer/agentic`: aceptar **200** (`completed`) y **202** (`awaiting_human_review`) como estados de éxito de corrida.
  - `POST …/answer/agentic/{thread_id}/resume` con `decision: approve | reject | adjust` (+ `adjusted_answer` / `note` cuando aplique).
  - 404 thread desconocido / 503 sin key / network → error visible.
- Transcript (template `ai-chat`): turno usuario = pregunta; turnos/sistema o tool-calls = pasos de `agent_trace`; burbuja assistant = `answer` cuando exista.
- Estado `awaiting_human_review`: mostrar `review_reasons` (+ confidence / flags útiles) y acciones Approve / Reject / Adjust; Adjust permite editar texto antes de resume.
- Citas: listar `source_path` + `excerpt` (preferir componente Astryx `Citation` donde encaje; si no, List/Item como E1).
- Loading: deshabilitar submit/resume duplicados mientras hay request in flight.
- Documentar caveat **MemorySaver**: si el backend se reinicia/reloadea, el `thread_id` pausado deja de servir (404) — aviso breve en UI o AGENTS.md front.
- `NEXT_PUBLIC_API_BASE_URL` sin cambios de contrato (ya documentado en E1).

## Approach sketch
```text
frontend/app/
  answer/page.tsx          ← scaffold ai-chat; wire agentic + gate
  lib/api/answer.ts        ← extender o sibling agentic.ts (tipos + fetch)
  components/app-shell.tsx ← label/nav si hace falta
backend: sin cambios de API (solo consumo)
```

Flujo UI:
1. Submit → `POST /answer/agentic`
2a. `completed` → mostrar answer + citations + trace
2b. `awaiting_human_review` → panel gate con reasons → resume → resultado final (`completed` / `rejected`)

`astryx build` (idea agentic + human review) → template **`ai-chat`**; alternativa layout `ai-chat-landing` solo si el transcript sobra (no preferido para E2).

## Impact
- frontend: upgrade `/answer` a chat agentic (template `ai-chat`), cliente API agentic/resume, estados gate, citas/traza, docs
- backend: ninguno (API ya en `development`)

## Open questions
- ¿Misma ruta `/answer` con modo Agentic (default) + Sync opcional, o solo agentic y sync queda atrás? **Propuesta:** misma `/answer`, **agentic por defecto**; toggle Sync opcional si el costo es bajo, si no defer sync a link secundario / dejar página previa solo si hace falta demo.
- ¿Artifact panel del template para citas/traza o todo inline en el transcript? **Propuesta:** traza + gate inline; citas en panel artifact o lista bajo la respuesta — decidir en apply tras ver scaffold real.
- ¿Mostrar `thread_id` al operador? **Propuesta:** sí, en metadata (debug / resume manual), no como hero.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-agentic-chat-ui`
