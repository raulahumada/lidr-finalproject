# Draft: add-agentic-orchestrator

## En una frase
Hoy la respuesta agentic es una **línea de montaje fija**. Este change la convierte en una **fábrica con jefe (orquestador)**: varios especialistas de rol + un hub que elige el próximo paso. Eso es el “multiagente” del curso. Ventas/Cobranzas son el **tema** de la pregunta (etiqueta), no cinco chatbots aparte en v1.

## Surface
- Primary: **both**
- Backend: `domain/graph/` (`orchestrator`, `build` estrella, `catalog`, `routing_history`, domain tag), `config.py`, `GET` catálogo
- Frontend: `/answer` (progress + dominio + rutas); `/agents` Astryx (catálogo + knobs); SideNav
- Course: `session_16` `domain/graph/supervisor/` — estrella `supervisor ⟷ agentes`, `Command(goto)`, gate, least privilege
- Peer Cristian: `orchestrator.py` (escalera determinista + max steps), `catalog.py` + `GET /config`, UI `/agents` + `/agents/flow`
- Patterns: estrella (curso) + frenos deterministas + catálogo único (peer); **nombres Metropol**

## Intent
Pasar de pipeline lineal a grafo multiagente con orquestador auditable, visible en UI y configurable; etiquetar dominio Metropol en la corrida.

## Arquitectura simple

### Hoy (línea — ya implementado)
```text
pregunta → enmarcar → buscar → escribir → chequear citas → ¿humano? → fin
```
Nadie decide: el orden está cableado en `build.py`.

### Después (estrella — este change)
```text
                 ┌─ intent_framer ────┐
                 ├─ corpus_fetcher ───┤
pregunta → ORQUESTADOR ⟷ ├─ grounded_composer ─┤ → escalation_gate → fin
                 ├─ source_guard ─────┤
                 └─ (vuelve al hub) ──┘
```
El hub elige el siguiente especialista (escalera legal + tope de pasos) y deja `routing_history`.

### Relación curso / Cristian / Metropol
| | Curso S14 | Cristian | Metropol v1 |
|---|-----------|----------|-------------|
| Forma | Estrella + supervisor | Estrella + orchestrator | Estrella + `orchestrator` |
| Cómo elige | LLM supervisor | Escalera determinista | **Escalera determinista** (como Cristian) |
| Especialistas | Estimación (NDA, budget…) | planner/retriever/synth/validator | `intent_framer` / `corpus_fetcher` / `grounded_composer` / `source_guard` |
| Dominio negocio | N/A | filtros seguros | tag `ventas\|cobranzas\|operacion\|tenela\|general` |

## Especialistas de pipeline (por qué existen)

No son departamentos de Metropol. Son **estaciones de la fábrica de una respuesta RAG**:

| Nodo | Trabajo | Si falta |
|------|---------|----------|
| `orchestrator` | Elige el próximo paso | Solo hay una lista fija (no multiagente) |
| `intent_framer` | Deja la pregunta buscable (+ memoria) | Retrieve basura |
| `corpus_fetcher` | Único que busca en el corpus | Sin evidencia / inventa |
| `grounded_composer` | Escribe con citas | Sin respuesta grounded |
| `source_guard` | Tira citas inventadas | Mentís con fuentes |
| `escalation_gate` | Pausa si hay duda | Entregás mal con confianza |

## Dominios Metropol (etiqueta, no nodos LLM en v1)

| Dominio | Por qué (cliente) |
|---------|-------------------|
| `ventas` | Captación, ofertas, dictamen |
| `cobranzas` | Planes, promesas, handoff cobranzas |
| `operacion` | Omnicanalidad, campañas, handoff |
| `tenela` | Core identidad / gestiones |
| `general` | Sin señal clara |

Se detectan (o se fuerzan en UI), van en el state, sesgan prompt/retrieve liviano y se muestran como chip. **Agentes dominio como nodos LLM = follow-up.**

## UI — dónde se ve y se configura

| Dónde | Qué |
|-------|-----|
| `/answer` | Progress/traza: pasos del orchestrator + motivo; chip de dominio; select Auto\|Ventas\|… |
| `/agents` (nuevo, SideNav) | Catálogo (rol, LLM-driven?, tools); vista del flujo; knobs |
| API | `routing_history`, `domain`, `agent_trace` |

### Knobs
| Knob | Dónde | Default |
|------|--------|---------|
| `AGENTIC_ORCHESTRATOR_MAX_STEPS` | env / Settings | 8–12 |
| `AGENTIC_CONFIDENCE_THRESHOLD` | ya existe | 0.55 |
| Dominio override | request + UI chat | `auto` |
| Catálogo | `GET /api/v1/answer/agents` | read-only |

## Graphify notes
- Hubs: `build_agentic_answer_graph` (hoy lineal), `AgenticAnswerRunner`, `GraphActivityLog`, `answer/page.tsx`
- Extender `build.py` + `orchestrator.py` + `catalog.py`; no isla paralela fuera de `domain/graph/`

## Non-goals (v1)
- Supervisor LLM S14
- Un nodo por dominio Ventas/Cobranzas con LLM
- Profiles multi-modelo en DB
- Loops re-query (composer pide otro retrieve)
- Auth; reemplazar `POST /answer` sync

## Draft requirements
- Grafo estrella: hub + return edges; mismos especialistas
- Escalera legal + step budget; `routing_history` en state/response/progress
- `domain` auto + override; sesgo ligero framer/composer
- `GET /answer/agents` catálogo (SSOT)
- UI `/answer`: dominio + routing; UI `/agents` Astryx: catálogo + knobs (valores desde API/env)
- `config` + `.env.example` + tests + `AGENTS.md`

## Approach sketch
```text
backend/app/domain/graph/
  orchestrator.py  catalog.py  build.py (STAR)
  agents/*  gate.py
api → GET /answer/agents
frontend /answer + /agents (Astryx SideNav)
```

## Practices check
- Aligned: domain/graph; routers finos; settings en config
- Deviations: escalera vs LLM supervisor (como peer); dominio = tag
- Risks: hub sin frenos → loops; catálogo solo en front → drift

## Impact
- backend: orchestrator, catalog, build, state, activity, schemas, tests, docs
- frontend: progress/domain; página `/agents`

## Open questions (resueltas en draft)
- UI: **`/agents`** en SideNav
- Override dominio en chat: **sí**
- Re-query loops: **no en v1**

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-agentic-orchestrator`
