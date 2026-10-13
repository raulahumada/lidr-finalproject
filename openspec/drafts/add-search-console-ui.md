# Draft: add-search-console-ui

## Surface
- Primary: **frontend**
- Paths: `frontend/app/search/page.tsx` (o similar), client `lib/api/search.ts`, SideNav link, `frontend/AGENTS.md`
- Course: N/A (Streamlit)
- Peer Cristian: consola búsqueda / retrieval UI (mapa E3 en draft `add-answer-chat-ui`)
- Backend: `POST /api/v1/search` **ya existe** — sin cambios API en v1

## Intent
Pantalla operador para **inspeccionar retrieve** (query → top-k chunks con score/path/excerpt) sin pasar por el LLM. Útil para debug de corpus y demos de RAG.

## Graphify notes
- Hubs: `POST /search`, `SemanticRetriever`, AppShell SideNav
- Gap: no hay ruta `/search` en frontend hoy

## Non-goals
- Ingesta / rebuild corpus desde UI
- Cambiar embeddings o ranking
- Auth
- Mezclar search dentro del chat `/answer` (pantalla aparte)

## Draft requirements
- Ruta `/search` en AppShell (SideNav)
- Form: query + k opcional → `POST {API}/api/v1/search`
- Lista Astryx (List/Table): score, source_path, excerpt; empty/error/503 states
- `astryx` workflow; sin `<div>` ad-hoc
- Smoke en `frontend/AGENTS.md`
- `tsc --noEmit`

## Approach sketch
1. `lib/api/search.ts` tipado
2. `astryx build` / template → page
3. Wire SideNav
4. Docs

## Practices check (backend | both only)
N/A — frontend only (salvo doc API ya existente).

## Impact
- frontend: page + client + nav + docs
- backend: none

## Open questions
- ¿Query params `?q=` deep link? → **Default: sí** (opcional nice-to-have en tasks)
- ¿Reusar Markdown para excerpts? → **Default: Text/List description**

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change 
- Promoted to openspec change `add-search-console-ui`
