# Draft: polish-answer-chat-ui

## Surface
- Primary: **frontend**
- Paths in this repo: `frontend/app/answer/page.tsx`, `frontend/AGENTS.md`; optionally small helpers colocated under `frontend/app/answer/` if the page grows
- Course reference (`session_16` / `ai-service`): UI is Streamlit/dashboard en el peer — **no** plantilla Next; tomar solo la idea de “respuesta primero, auditoría secundaria”. Capas del curso no aplican a este change.
- Patterns borrowed (not copied): Astryx `ai-chat` frame ya en uso; `Collapsible` / `CollapsibleGroup` para audit; sin contratos API nuevos

## Intent
El chat `/answer` ya muestra respuesta, ruteo, tool calls, aportes custom y evidencia, pero compiten en el mismo plano: el operador pierde la respuesta detrás del flujo. Este change **reordena y colapsa** la superficie de auditoría para una demo clara: respuesta → aportes → evidencia; ruteo/pasos detrás de un disclosure.

## Graphify notes
- Queried: `answer chat page routing custom notes evidence tool calls UI`
- Hubs: `AnswerPageInner` / `answer/page.tsx`, `CustomNotesList`, `runAgenticWithProgress`, `agentic.ts`
- Edges: UI ya consume `custom_notes` / `routing_history` / `agent_trace` / citations; no hace falta tocar runner
- Gaps: none for frontend polish

## Non-goals
- Cambios de API / schemas / runner / session store
- Rediseño de `/agents` o AppShell/home boilerplate (follow-up aparte)
- Nuevos endpoints o tipos compartidos monorepo
- Evaluaciones RAGAS / calidad de grounding (producto aparte)
- Auth

## Draft requirements
- En un turno assistant (live terminal + history), el orden visual SHALL ser:
  1. **Respuesta** (Markdown) — o estado rejected / draft en review
  2. **Aportes custom** (si hay) — texto wrapping, preview acotado
  3. **Evidencia** (si hay citas)
  4. **Auditoría** (ruteo + flujo/tool calls / domain chip) — **colapsada por defecto** al terminar; expandida o visible en vivo mientras `running`
- Mientras `running`: domain + progreso (tool calls) visibles; ruteo/notas pueden mostrarse sin esconder el mensaje “corriendo…”
- En history turns: misma jerarquía (hoy history muestra respuesta + notas + evidencia sin ruteo — OK; si hay notas, quedan encima de evidencia)
- Usar componentes Astryx (`Collapsible` / List / Chat* existentes); sin `<div>` + CSS ad-hoc
- Actualizar smoke en `frontend/AGENTS.md`
- `npx tsc --noEmit`

## Approach sketch
1. Extraer un bloque pequeño `RunAudit` / reordenar JSX en `AnswerPageInner` (live + terminal + history).
2. Envolver “Ruteo” + `ChatToolCalls` (y opcionalmente domain) en `Collapsible` con label tipo “Flujo / auditoría”; `defaultIsOpen={isCurrentBusy}` o similar.
3. Mover `CustomNotesList` y evidencia **debajo** de la respuesta en el branch terminal (hoy notas/ruteo van *antes* del Markdown).
4. No tocar `lib/api/*` salvo que haga falta un tipo local de presentación.
5. Docs + tsc; `graphify update .` post-apply.

## Practices check (backend | both only)
N/A — surface frontend only.

## Impact
- frontend: `/answer` hierarchy + collapsible audit + AGENTS.md
- backend: none

## Open questions
- ¿Incluir domain Badge dentro del Collapsible o dejarlo siempre visible? → **Default: chip siempre visible** (compacto); ruteo/tool calls adentro.
- ¿Home/AppShell Astryx en este change? → **No** (non-goal); otro draft si hace falta.
- ¿History también muestra Collapsible vacío sin ruteo? → **No render** si no hay contenido de auditoría.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `polish-answer-chat-ui`
- Synced to main specs + archived `2026-10-13-polish-answer-chat-ui`
