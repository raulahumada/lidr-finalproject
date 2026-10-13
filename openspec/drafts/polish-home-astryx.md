# Draft: polish-home-astryx

## Surface
- Primary: **frontend**
- Paths: `frontend/app/page.tsx`, posiblemente shell copy; `frontend/AGENTS.md`
- Peer: web-console home modules; curso Streamlit — no plantilla

## Intent
Sacar el boilerplate de `create-next-app` de la home: **entrada de producto Metropol** (brand + CTA a `/answer` y `/agents`) con Astryx, alineada al shell ya existente.

## Graphify notes
- Hub: AppShell / `page.tsx` home
- No tocar agentic APIs

## Non-goals
- Dashboard de métricas / usage (peer late-stage)
- Auth
- Rediseñar `/answer` o `/agents` de nuevo

## Draft requirements
- Home: hero de producto (Metropol / LiDR entrega) + CTAs a chat y agentes
- Solo componentes Astryx; theme tokens
- Mobile ok
- Docs mínimos en `frontend/AGENTS.md`

## Approach sketch
1. `astryx build` / template landing o empty+CTA
2. Links SideNav consistentes
3. `tsc`

## Practices check
N/A — frontend only.

## Impact
- frontend: home
- backend: none

## Open questions
- ¿Copy en español formal Metropol? → **Default: sí**

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change 
- Promoted to openspec change `polish-home-astryx`
