# Draft: add-rag-answer-with-cag

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/generation/cag/` (response caches), knowledge-pack renderer under `generation/rag/` or `foundation/prompts/`, `backend/app/foundation/prompts/` (Jinja), `backend/app/domain/` (conductor), `backend/app/generation/rag/` (reuse retriever/embedder), `backend/app/api/routes/answer.py`, `backend/app/schemas/`, `backend/app/config.py`, `backend/requirements.txt`, `backend/.env.example`, root `docker-compose.yml` (Redis Stack), `AGENTS.md`
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/` @ `d2f015f`
- Peer reference (gitignored): `cahumada/lidr-master` → `.reference/lidr-master/` — sync: `bash .cursor/skills/openspec-prespec/scripts/sync-peer-lidr-master.sh`
- Patterns borrowed (not copied):
  - **Curso — Response CAG:** `generation/cag/exact.py` + `semantic.py`; conductor; hermanos de `generation/` no se importan entre sí
  - **Curso — Jinja:** `foundation/prompts/<use_case>/<version>/{system,user}.j2` + loader `StrictUndefined`
  - **Peer (Cristian / lidr-master) — Knowledge CAG:** `ai-service/app/generation/rag/process_map/cag.py` + spec `openspec/specs/process-map` / `answer-generation`
    - Precargar un **mapa/contexto curated** en el prompt (no el corpus entero)
    - Medir tamaño con el **mismo tokenizer** que el chunker (tiktoken), no chars
    - Si supera techo → **fallar el build** (nunca truncar en silencio)
    - Incluir límites (“qué es / qué NO es”) **dentro** del contexto precargado
    - `DROP_ORDER` documentado si algún día hay que recortar secciones
  - Dominio VisualTIME / estimador **no** se copia; adaptar a mapa/pack **Metropol** (omnicanalidad, agentes, handoff, Tenela)

## Intent
Exponer **`POST /api/v1/answer`**: pregunta en lenguaje natural → respuesta grounded sobre el corpus Metropol, con:

1. **Knowledge CAG** (peer lidr-master) — contexto precargable curated (mapa Metropol / reglas / límites), render medido en tokens, techo duro, inyectado en **system** vía Jinja (`{{ knowledge_pack }}`). No corpus completo.
2. **Response CAG** (curso) — caché exacta + semántica de respuestas en Redis Stack.
3. **RAG** — retrieve top-k desde pgvector inyectado en **user** vía Jinja.
4. **Citas** — fuentes (`source_path`, chunk ids / excerpts) + `cached`.

## Non-goals
- UI / frontend / chat Astryx (sigue `/answer` API-only)
- LangGraph / multiagente / supervisor (siguiente slice)
- Guardrails completos de moderación/PII del curso (mínimo: “sin evidencia → no inventar” en system prompt; guardrails foundation opcionales después)
- Meter el corpus completo en el system prompt (knowledge pack acotado por tokens)
- Hybrid search, HNSW, re-ranker, streaming SSE (salvo que quepa trivial)
- Ingest de xlsx/pptx/media
- Auth de servicio / API keys (fuera de este change salvo settings stub)

## Draft requirements
- Añadir **Redis Stack** al Compose local (mismo patrón curso: RediSearch para semantic cache; documentar en `AGENTS.md`).
- Settings: `REDIS_URL`, TTL caches, umbral semántico, `SEMANTIC_CACHE_LOG_ONLY` (calibrar sin servir hits), `ANSWER_PROMPT_VERSION`, path/nombre del knowledge pack, modelo chat (`OPENAI_*` / chat model distinto del embedder), `k` default.
- Paquete `app/generation/cag/`:
  - `exact.py` — clave SHA-256 de `{prompt_version, model, k, question, …}`; get/set Redis; fallos Redis → miss (no 500).
  - `semantic.py` — bucket p.ej. `prompt_version:model:k` + embedding de la pregunta; lookup/store con umbral; `log_only` mode.
- Paquete `app/foundation/prompts/`:
  - Loader Jinja2 versionado.
  - Templates `answer/v1/system.j2` (rol + `{{ knowledge_pack }}`) y `answer/v1/user.j2` (`{{ question }}` + `{{ retrieved_chunks }}`).
- **Knowledge CAG renderer** (inspirado en peer `process_map/cag.py`, dominio Metropol):
  - Armar texto precargable (límites + secciones curated: p.ej. glosario agentes, handoff, qué no inventar).
  - `count_tokens` (tiktoken / mismo encoding que chunker) + `KNOWLEDGE_PACK_MAX_TOKENS`.
  - Si excede → error explícito en build/load (no truncar).
  - Contenido versionado en repo (`data/` o `foundation/prompts/answer/knowledge/`); v1 puede ser Markdown estático renderizado; grafo tipo process-map Metropol queda como follow-up si hace falta.
- Conductor `app/domain/answer_service.py` (o nombre equivalente):
  1. exact cache lookup → hit return  
  2. semantic lookup → hit return  
  3. RAG retrieve (`SemanticRetriever`)  
  4. si 0 chunks → respuesta “sin evidencia” **sin** LLM (o con LLM explícitamente limitado; preferir sin LLM)  
  5. render Jinja system+user → LLM chat → parse answer + citations  
  6. store exact + semantic  
- API: `POST /api/v1/answer` con schema request (`question`, `k` opcional) y response (`answer`, `citations[]`, `cached`: `exact|semantic|false`, `prompt_version`, latencia).
- Sin `OPENAI_API_KEY` → **503** (igual que search). Redis down → degradar a miss (seguir generando).
- Tests: exact hit; miss path con LLM mock; empty corpus / no evidence; semantic `log_only` no sirve hit; router contract.
- Docs: curl en `AGENTS.md`; `.env.example` actualizado.

## Approach sketch
```text
POST /api/v1/answer
  └→ api/routes/answer.py          (fino)
       └→ domain/answer_service.py (conductor)
            1. generation/cag/exact
            2. generation/cag/semantic
            3. generation/rag/retriever  (ya existe)
            4. foundation/prompts (Jinja system+user + knowledge pack)
            5. foundation/llm (thin OpenAI chat wrapper — nuevo, mínimo)
            6. cag.store
```

Capas: `cag` ↛ `rag` y viceversa; solo el conductor los une. Composition root en `dependencies.py`.

Knowledge CAG ≠ response CAG: el pack va en system; los chunks RAG van en user; los caches guardan el **JSON de respuesta** ya validado.

## Practices check (backend | both only)
- Aligned: routers finos; settings vía `get_settings()`; schemas request/response; deps en `requirements.txt` con piso; capas curso como forma (`foundation` / `generation` / `domain` conductor); secretos por env; compose sin passwords hardcodeados (Redis sin auth local o pass desde `.env`).
- Deviations (+ why):
  - Semantic cache exige **Redis Stack** — igual que el curso; documentar.
  - Knowledge CAG sigue peer `process_map/cag.py` (medición/techo/límites); **no** copiamos grafo VisualTIME. El módulo de response cache sigue llamándose `generation/cag/` (curso); el preload knowledge puede vivir junto a rag/prompts para no mezclar con Redis caches.
  - LLM wrapper mínimo (sin Instructor/LiteLLM completo) en v1.
- Risks if ignored: truncar el pack en silencio; pack > techo; imports cruzados response-cag↔rag; cachear “sin evidencia”.

## Impact
- backend: cag, prompts Jinja, conductor answer, route/schemas, Redis Stack, tests, docs
- frontend: ninguno

## Open questions
- ¿Contenido inicial del knowledge pack Metropol? **Propuesta:** v1 Markdown curated (límites + handoff + “no inventar”) con techo de tokens; grafo tipo process-map del peer como follow-up si el corpus lo pide.
- ¿Structured output en v1? **Propuesta:** JSON ligero (`answer` + `citation_indices`).
- ¿Semantic cache `log_only` default? **Propuesta:** sí, hasta calibrar umbral.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-rag-answer-with-cag`
- Specs synced, archived as `2026-10-08-add-rag-answer-with-cag`
