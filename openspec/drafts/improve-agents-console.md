# Draft: improve-agents-console

## Surface
- Primary: **both**
- Backend: perfiles **custom** en Postgres (Alembic); builtins siguen en código/Jinja y se listan read-only; CRUD solo para customs; catálogo unificado; ladder + nodo genérico para customs
- Frontend: `/agents` — ver builtins (prompt Jinja si aplica), crear/editar/borrar customs, ver flujo; Astryx; docs
- Course reference (`session_16`): supervisor + prompts Jinja; CRUD de agentes = producto (peer), no requisito del curso
- Patterns: builtins = código + Jinja; customs = filas DB; API SSOT para la consola

## Intent
Consola de agentes: inspeccionar los del pipeline Metropol (fijos) y **crear/editar agentes nuevos** persistidos en BD (prompt + rol), enganchados al ladder vía un especialista LLM genérico.

## Graphify notes
- Hubs: `catalog.py`, `AgentsPage`, `grounded_composer` → Jinja, `persistence/models`
- Builtins no se mutan; nueva entidad `agent_profiles` solo customs (+ seed no aplica a override de builtins)

## Modelo de producto

| Clase | Origen | UI | Persistencia |
|-------|--------|-----|--------------|
| **Builtin** | Código + Jinja (`answer/v2/system.j2` para composer) | **Solo lectura** (label, role, prompt preview, tools) | No se edita ni borra desde API |
| **Custom** | Creados en `/agents` | Crear / editar / borrar | Postgres |

- Retrieve, gate, orchestrator, etc. siguen siendo nodos de código; no se “clonan” como custom con otra lógica.
- Custom = agente LLM (`prompt_specialist`) con `system_prompt` (y metadatos) en DB, insertable en el ladder.

## Non-goals
- PATCH/DELETE de builtins; reescribir `.j2` desde la UI
- Generar módulos Python nuevos desde el browser
- Supervisor LLM; auth; editor drag-drop avanzado

## Draft requirements
- `GET /answer/agents` — builtins (read-only, con `prompt_preview` desde Jinja cuando `llm_driven`) + customs desde DB + ladder + knobs
- `GET /answer/agents/{key}` — detalle; 404 si no existe
- `POST /answer/agents` — crea custom en DB (`key`, label, role, system_prompt, enabled); 409 si key choca con builtin o custom existente
- `PATCH /answer/agents/{key}` — solo custom; si key es builtin → **405/422**
- `DELETE /answer/agents/{key}` — solo custom; builtin → **405/422**
- Ladder: incluir customs enabled; legalidad/presupuesto de pasos se mantienen; builtins siempre presentes en el catálogo aunque un custom se inserte en el orden
- UI: lista (badge builtin vs custom); detalle read-only para builtin; forms crear/editar solo custom; sección flujo
- Tests API (bloqueo de mutación builtin); `tsc`; docs

## Approach sketch
```text
backend/
  alembic + AgentProfileRow          # solo customs
  domain/graph/agent_store.py        # CRUD customs
  domain/graph/catalog.py            # merge builtins (código) + customs (DB)
  domain/graph/agents/prompt_specialist.py
  orchestrator / build               # ladder con keys custom
  api/routes/answer_agents.py
frontend/
  app/agents/page.tsx                # studio
  lib/api/agents.ts
```

Prompt builtin composer: **solo** lectura desde Jinja (`ANSWER_PROMPT_VERSION`). Prompt custom: **solo** DB.

## Practices check (backend | both only)
- Aligned: persistencia foundation; dominio graph; routers finos; Jinja intacto para builtins
- Deviations: nodo genérico + ladder dinámico para customs
- Risks: keys reservadas (builtins); max steps; validar body PATCH

## Impact
- backend: migration, store, catalog merge, prompt_specialist, routes, tests
- frontend: studio `/agents`, types, docs

## Open questions (defaults)
- ¿Editar orden del ladder en este change? → **Sí, mínimo** (incluir/quitar customs enabled; builtins fijos en posiciones legales o ladder configurable con constraints).
- Default ladder insert for custom: **después de `corpus_fetcher`, antes de `grounded_composer`** (o al final antes del gate) — fijar en design al propose.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `improve-agents-console`
