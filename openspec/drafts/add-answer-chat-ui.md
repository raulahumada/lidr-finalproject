# Draft: add-answer-chat-ui

## Surface
- Primary: **frontend**
- Paths in this repo: `frontend/app/` (ruta chat), cliente HTTP hacia API, shell/nav Astryx; opcional `frontend/.env.example` (`NEXT_PUBLIC_API_BASE_URL`)
- Reuse backend (sin reimplementar): `POST /api/v1/answer`, más adelante `/answer/agentic` + resume
- Course reference: UI del curso es **Streamlit** mínima (`streamlit_app.py` → form → `POST /estimate`); forma útil = “pantalla que llama API y muestra resultado”, no consola completa
- Peer reference (patrón, no copiar shadcn/auth verbatim): `lidr-master/business-backend` consola Next
- Patterns borrowed (not copied):
  - Consola con módulos (Respuesta / RAG / Config) — nosotros: etapas
  - Chat con citas + gate humano (peer `/answer` agentic + live progress)
  - Astryx kit (este repo) en lugar de shadcn del peer
  - Dominio Metropol Fintech

## Intent
Empezar la UI de producto **por etapas**. Esta draft define el **mapa completo** (Cristian + curso) y el **slice 1**: chat sync sobre `POST /answer` (pregunta → respuesta + citas), cableado al shell Astryx ya existente.

## UI map (peer Cristian vs curso vs nosotros)

| Área (peer) | Curso | Metropol (plan por etapas) |
|-------------|-------|----------------------------|
| Chat agentic + traza + gate + progress polling | Streamlit estimate (form → texto) | **E1** chat sync `/answer`; **E2** agentic + resume |
| Búsqueda `/search` | — | **E3** |
| Ingesta preview documentos | — | **E4** (CLI sigue siendo source of truth al inicio) |
| Corpus rebuild (admin) | — | **E5+** / defer |
| Agentes / perfiles LLM | — | defer (backend aún sin config API) |
| Models / providers / usage | — | defer |
| Auth / users / roles | — | defer |
| Business DB | — | out of scope (dominio Visual Time) |

## Roadmap de etapas (cambios OpenSpec separados)

1. **`add-answer-chat-ui` (este draft)** — Chat sync: input, loading, answer, citas, errores 503; link en shell; `NEXT_PUBLIC_API_BASE_URL`
2. **`add-agentic-chat-ui`** — Modo agentic: `agent_trace`, 202 → UI de revisión humana → resume (approve/reject/adjust). Sin `/start`+progress hasta que exista en API
3. **`add-search-console-ui`** — Pantalla búsqueda semántica (`POST /search`)
4. **`add-ingest-preview-ui`** — (opcional) preview de chunking / estado; no reemplaza CLI
5. Más adelante — admin corpus, agentes, auth, usage (solo si el backend expone contratos)

## Non-goals (este change / E1)
- Agentic, resume, progress polling, sesiones multi-turno
- Auth, admin, corpus rebuild, providers
- Copiar UI shadcn/peer verbatim; inventar layout con `<div>` sin Astryx
- Cambios de API backend (salvo doc de URL pública si hace falta)
- Streamlit

## Setup previo (hecho / en curso)
- Astryx `0.6.8` + `@astryxdesign/theme-stone`; `astryx init --all`; `theme add stone --import`
- Theme default **stone** vía `src/astryx-themes.ts` + `Providers` / `globals.css` / `data-astryx-theme="stone"`
- `.npmrc` con `legacy-peer-deps=true` (peer opcional `theme-neutral` del CLI)

## Draft requirements (solo E1)
- Ruta de chat (p. ej. `/answer` o `/chat`) en el shell junto a items/settings.
- Formulario: pregunta + opcional `k`; llama `POST {API}/api/v1/answer`.
- Estados: idle / loading / success (answer + lista de citas con path/excerpt) / error (503 sin key, red, 4xx/5xx).
- Cliente fetch tipado mínimo en front (sin package compartido monorepo).
- `NEXT_PUBLIC_API_BASE_URL` default `http://localhost:8000`; documentar en `frontend` / `AGENTS.md`.
- Workflow Astryx: `astryx build` → template/components antes de maquetar.

## Approach sketch
```text
frontend/app/
  layout.tsx + AppShellLayout (existente)
  answer/page.tsx (o chat/)  ← E1
  lib/api/answer.ts          ← cliente thin
backend: sin cambios (E1)
```

## Graphify notes
- Queried: frontend chat / answer / Astryx
- Hubs: `app/page.tsx`, `AppShellLayout`, `answer()` / `AnswerService` (contrato a consumir)
- Extender shell nav; no inventar segundo layout
- Gaps: UI de chat aún no existe en el grafo (esperado)

## Impact
- frontend: ruta chat sync + cliente API + nav + env example/docs
- backend: ninguno en E1

## Open questions
- ¿Ruta `/answer` (como peer) o `/chat`? **Propuesta:** `/answer` para alinear con API.
- ¿E1 usa solo sync y deja toggle agentic para E2? **Propuesta:** sí.
- ¿CORS ya cubre `localhost:3000`? Sí por default en backend; verificar al probar.

## Status
- [x] User approved — proposed as `openspec/changes/add-answer-chat-ui/` (solo E1)
