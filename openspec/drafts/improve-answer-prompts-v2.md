# Draft: improve-answer-prompts-v2

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/foundation/prompts/answer/v2/`, `backend/app/foundation/prompts/loader.py`, `backend/app/generation/rag/` (context block builder), `backend/app/domain/answer_service.py`, `backend/app/foundation/llm/chat.py` (si hace falta parse), `backend/app/config.py` (`ANSWER_PROMPT_VERSION=v2`), tests, `AGENTS.md`
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/` @ sync reciente
  - `foundation/prompts/` Jinja versionado (`estimation/v1..v3`)
  - RAG grounded (S9+): `context_assembler.build_context_block` → bloques `<source id="…" document_id="…">`, `truncate_to_token_budget`, system prompt que exige citar solo esos `id`, `validate_citations` + reintento correctivo
  - `prompt_version` entra en claves de CAG
- Peer reference: `.reference/lidr-master/` — `answer/v1..v3` (prosa + “Fuentes citadas”, respuesta parcial, bloques numerados con procedencia, persona/guardrails subordinados)
- Patterns borrowed (not copied):
  - **Curso:** contexto con procedencia visible + techo de tokens; citar solo ids presentes; versionar prompts; no editar v1 in-place
  - **Peer:** síntesis en prosa, respuesta parcial explícita, cierre de fuentes; unificar bloques (no volcar chunks)
  - Dominio Metropol (no VisualTIME / no estimador de horas)

## Intent
Subir la calidad de `/answer` alineando el armado de prompts al curso (bloques de evidencia citables + budget) y al peer (redacción / respuesta parcial), sin tocar agentes todavía.

Default `ANSWER_PROMPT_VERSION=v2` (invalida cachés exactas viejas de v1).

## Non-goals
- LangGraph / multiagente / perfiles de agente (persona/guardrails opcionales mínimos o defer)
- Memoria multi-turno / business-db (peer v2/v3) — follow-up
- Cambiar modelo de embeddings o chunking
- Frontend
- Instructor/LiteLLM completo del curso (seguir JSON mode o parse de “Fuentes citadas” + map a `citations[]`)
- Eval RAGAS formal (opcional después)

## Draft requirements
- Añadir `answer/v2/system.j2` + `user.j2`:
  - System: rol Metropol + reglas numeradas (solo contexto; respuesta parcial; no inventar; handoff; knowledge pack subordinado).
  - User: pregunta + contexto formateado en bloques numerados con procedencia (`source_path`, opcional section/strategy, `chunk_id` o índice estable).
- Builder de contexto (estilo curso `build_context_block` / peer `render_hit_block`): un bloque por hit; mismo texto que se envía (un solo renderer).
- Techo de tokens del contexto recuperado (`MAX_ANSWER_CONTEXT_TOKENS` o reusar setting); truncar por bloques enteros (no cortar mid-chunk en silencio sin documentar).
- Citas: preferir ids/índices que existan en los bloques enviados; validar y dropear fabricados (curso `validate_citations` liviano); si el modelo usa prosa “Fuentes citadas:”, parsear a `citations[]`.
- Default settings → `answer_prompt_version=v2`; documentar flush Redis al cambiar versión.
- Tests: render v2 incluye procedencia; partial-answer wording en system; citation id inventado se filtra; loader StrictUndefined.
- No borrar v1 (queda disponible vía setting).

## Approach sketch
```text
retrieve → fit_to_budget(hits) → render_hit_blocks
  → Jinja answer/v2 (system + knowledge_pack; user + question + context)
  → LLM → parse answer + cite ids → validate against sent hits → AnswerResponse
```

Caché exacta ya incluye `prompt_version` → v2 no choca con respuestas v1 cacheadas.

## Practices check (backend | both only)
- Aligned: prompts en `foundation/`; conductor sigue en `domain/`; routers finos; settings vía `get_settings()`; versionado en vez de editar v1.
- Deviations: sin Instructor schema validators del curso en este slice (parse + validate ids en conductor); formato de bloque puede ser markdown numerado estilo peer o XML `<source>` estilo curso — **propuesta: bloques markdown numerados + id estable (índice o chunk_id)** más simple para Q&A Metropol; XML opcional si queremos 1:1 curso.
- Risks if ignored: editar v1 in-place sin bump → caché sirve respuestas viejas; citar paths no enviados; overflow de contexto.

## Graphify notes
- Hub: `AnswerService` (21 edges) — community **Answer API & Dependencies**
- Path: `AnswerService` ← `answer_service.py` → `render_answer_prompts()` (2 hops)
- Touch set for v2: `loader.py`, `answer/v1` → add `v2`, `knowledge_pack.py`, `ChatClient`, `ExactAnswerCache` / `SemanticAnswerCache` (prompt_version in keys), `get_answer_service()`, tests `test_answer_service.py`
- Communities: Prompt Templates Init, Knowledge CAG Pack, Semantic Search API (hits → context blocks)
- CLI: `~/.local/bin/graphify` (uv tool `graphifyy`); ensure `PATH` includes `~/.local/bin`

## Impact
- backend: prompts v2, context builder, answer_service parse/validate, config default, tests, docs
- frontend: ninguno

## Open questions
- ¿XML `<source>` (curso) o bloques markdown numerados (peer)? **Propuesta: markdown numerados con `id=chunk_id` visible** — más legible para Q&A; mismo contrato de “solo citar ids vistos”.
- ¿Salida JSON (`answer` + `citation_indices`) o prosa + “Fuentes citadas”? **Propuesta: mantener JSON interno para API estable**, pero system v2 con reglas de síntesis/parcial del peer; indices deben mapear a bloques enviados.
- ¿Budget default? **Propuesta: 3000–4000 tokens de contexto retrieve** (aparte del knowledge pack).

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `improve-answer-prompts-v2`
- Specs synced, archived as `2026-10-08-improve-answer-prompts-v2`
