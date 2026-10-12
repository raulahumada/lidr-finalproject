# Draft: add-agentic-answer

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/domain/graph/` (state, agents, build, gate, runner), `backend/app/api/routes/answer_agentic.py`, schemas, `dependencies.py` / lifespan checkpointer, `requirements.txt` (`langgraph`), tests, `AGENTS.md`
- Reuse (no reimplement): `SemanticRetriever`, piezas de generación de `AnswerService` / prompts v2 / `context_blocks`, helpers de citas
- Course reference: `session_16` → `.reference/ai-engineering/ai-service/app/domain/graph/supervisor/` (StateGraph, least-privilege, `interrupt`) + forma `generation/agentic/`
- Peer reference (solo **patrón**, no nombres ni código): lidr-master grafo Q&A + gate condicional
- Patterns borrowed (not copied):
  - Pipeline de 4 especialidades + gate humano condicional (esencia curso/peer)
  - **Nombres propios Metropol** (no los de Cristian ni del estimador del curso):
    | Rol (esencia) | Nuestro nodo |
    |---------------|--------------|
    | Preparar / enmarcar la pregunta | `intent_framer` |
    | Recuperar evidencia del corpus | `corpus_fetcher` |
    | Redactar respuesta grounded | `grounded_composer` |
    | Auditar que las citas existan en lo recuperado | `source_guard` |
    | Pausar para humano si hace falta | `escalation_gate` |
  - LangGraph en `domain/`; HTTP fino; solo `corpus_fetcher` toca el retriever
  - Dominio Metropol Fintech

## Intent
Añadir **`POST /api/v1/answer/agentic`**: misma calidad de RAG/citas que `/answer`, en un grafo LangGraph con pasos auditables y escalamiento humano opcional (confianza baja / sin evidencia / citas inválidas).

`/answer` (sync un-shot) **se mantiene**.

## Non-goals
- Copiar nombres o módulos de Cristian (`query_planner`, `evidence_retriever`, …) ni agentes del estimador del curso
- Frontend / consola de agentes / polling UI
- Supervisor LLM que elige el próximo nodo en runtime — **v1: pipeline fijo** de los 4 nodos + gate
- Hybrid retrieve, rerank, decompose avanzado (`intent_framer` v1 = normalizar / pass-through)
- Multi-proveedor LLM / perfiles en DB / memoria multi-turno completa
- Checkpointer Postgres (v1: `MemorySaver`)

## Draft requirements
- Dep `langgraph` en `requirements.txt`.
- Estado tipado (p. ej. `AgenticAnswerState`): question, framed_query, hits, answer, citations, confidence/flags, review_reasons, `agent_trace`.
- Grafo:
  1. `intent_framer` — sin tools; prepara la query para retrieve
  2. `corpus_fetcher` — único nodo que llama `SemanticRetriever`
  3. `grounded_composer` — prompts v2 + `ChatClient` / lógica compartida con `/answer`
  4. `source_guard` — valida ids/índices contra hits; marca `citations_valid`
  5. `escalation_gate` — `review_reasons` puro; `interrupt()` solo si non-empty → HTTP **202** + resume
- API:
  - `POST /api/v1/answer/agentic` → 200 o 202
  - `POST /api/v1/answer/agentic/{thread_id}/resume` (approve / reject / adjust)
  - Response: `status`, `agent_trace`, answer/citations al completar
- Tests + docs curl en `AGENTS.md`.

## Approach sketch
```text
POST /api/v1/answer/agentic
  └→ api/routes/answer_agentic.py
       └→ domain/graph/runner.py
            StateGraph:
              START → intent_framer → corpus_fetcher
                   → grounded_composer → source_guard
                   → escalation_gate → END | interrupt
```

## Practices check (backend | both only)
- Aligned: router fino; grafo en `domain/`; reuse retriever/prompts; `get_settings()`; capas curso.
- Deviations: pipeline fijo (no supervisor LLM S14); `MemorySaver` local; nombres propios (no peer verbatim).
- Risks if ignored: segundo pipeline duplicado; gate que siempre pausa; copiar API/nombres del peer.

## Graphify notes
- Reusar hubs: `AnswerService`, `SemanticRetriever`, `ChatClient`, `context_blocks`.
- Tras apply: `graphify update .`

## Impact
- backend: grafo agentic Metropol + resume + tests + docs
- frontend: ninguno

## Open questions
- ¿CAG en agentic? **Propuesta:** no en el hot path v1; cache del resultado final opcional después.
- ¿Confidence? **Propuesta:** heurística (hits + citations_valid + no_evidence) + umbral en settings.
- ¿`/start` + progress? **Propuesta:** follow-up.

## Deferred (siguiente mejora, no este change)
- Hub `orchestrator` con escalera determinista (forma S14/peer, sin LLM router).
- Checkpointer `AsyncPostgresSaver` (hoy v1: `MemorySaver`).
- Supervisor LLM estilo S14.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to OpenSpec change `add-agentic-answer`
