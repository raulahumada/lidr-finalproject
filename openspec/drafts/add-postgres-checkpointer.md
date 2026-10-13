# Draft: add-postgres-checkpointer

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/domain/graph/checkpointer.py`, lifespan/`main.py` or deps wiring, `requirements.txt`, tests agentic, `AGENTS.md` / `frontend/AGENTS.md` (caveat copy only)
- Frontend: **ninguno** de contrato; solo docs si el texto MemorySaver cambia (resume sobrevive reload)
- Course reference: `session_16` / `ai-service` — `app/domain/graph/checkpointer.py` (`AsyncPostgresSaver` + `AsyncConnectionPool` + `setup()`), `langgraph-checkpoint-postgres`
- Peer reference: mismo patrón en `lidr-master/ai-service` (tablas LangGraph excluidas de Alembic autogenerate)
- Patterns borrowed (not copied):
  - Mismo Postgres que pgvector; tablas propias del saver (`checkpoints`, `checkpoint_writes`, `checkpoint_blobs`, `checkpoint_migrations`)
  - DSN libpq plano (strip `+psycopg` / `+asyncpg` de `DATABASE_URL`)
  - `setup()` idempotente al arranque; no migrar esas tablas con Alembic
  - Tests siguen pudiendo usar `MemorySaver` / reset

## Intent
Reemplazar el checkpointer agentic v1 (`MemorySaver` in-process) por un saver **Postgres**, para que pause/resume de LangGraph sobreviva reinicios de Uvicorn. Cierra el follow-up documentado en agentic-answer / live-progress.

## Graphify notes
- Queried: `MemorySaver checkpointer Postgres AsyncPostgresSaver agentic resume`
- Hubs: `checkpointer.py` (`get_checkpointer` / `reset_checkpointer`), `AgenticAnswerRunner` (compile + resume), tests `test_agentic_*`, routes `answer_agentic`
- Extender `checkpointer.py` + wiring de lifespan/deps; no inventar segundo grafo
- Gaps: activity log de live progress sigue in-process (fuera de este change salvo nota)

## Non-goals
- Persistir el **activity log** de `/progress` en Redis/Postgres (sigue in-process; progress “running” se pierde al reload, pero un thread **pausado** debe poder resumirse)
- Orchestrator hub / LLM supervisor
- Migrar todo el backend a async SQLAlchemy
- Alembic migrations para tablas LangGraph (las crea `setup()`)
- Cambios de UI o contratos HTTP (mismos thread_id / resume / start)

## Draft requirements
- Dep: `langgraph-checkpoint-postgres` (+ `psycopg_pool` si hace falta).
- Checkpointer de producción: Postgres sobre `DATABASE_URL` (mismo Compose Postgres).
- Al arranque de la app: abrir pool, `setup()` idempotente, inyectar saver en el grafo compilado.
- Tras reinicio del proceso API, un `thread_id` en `awaiting_human_review` MUST seguir siendo resumible vía `POST .../resume`.
- Tests: default/unit siguen con MemorySaver o reset aislado; al menos un test de integración (o marcado) que demuestre persistencia si hay DB; no romper suite actual.
- Documentar en `AGENTS.md`: caveat MemorySaver eliminado para resume; aclarar que activity/progress running sigue process-scoped.
- Excluir tablas `checkpoint*` del autogenerate Alembic si aplica (como peer).

## Approach sketch
```text
backend/app/domain/graph/checkpointer.py
  - saver_conninfo(DATABASE_URL) → postgresql://…
  - open/get Postgres saver + setup()
  - keep MemorySaver path for tests via env or reset helper

backend/app/main.py (lifespan) o dependencies
  - enter pool/saver at startup; compile graph with that checkpointer

runner.py
  - consume get_checkpointer() (ya lo hace); sin cambio de API

Alembic env.py (si hace falta)
  - include_object skip checkpoint_*
```

**Decisión de forma (curso Async vs nuestro sync):**  
Nuestro runner agentic es **sync** (`invoke` / `stream` en thread). Propuesta: usar el **`PostgresSaver` sync** de `langgraph-checkpoint-postgres` + pool sync, alineado al stack actual. Documentar desviación consciente vs curso/`AsyncPostgresSaver` (peer async). Si en apply el paquete o la versión solo favorece aio de forma limpia, evaluar `AsyncPostgresSaver` + bridge mínimo — preferir no reescribir el grafo a async en este change.

## Practices check (backend)
- Aligned: checkpointer en `domain/graph/`; settings `DATABASE_URL`; routers finos; tests; deps en `requirements.txt`.
- Deviations: sync `PostgresSaver` vs curso `AsyncPostgresSaver` (stack sync actual); tablas LangGraph vía `setup()` no Alembic (igual peer/curso).
- Risks if ignored: seguir perdiendo resumes al reload; autogenerate Alembic proponiendo DROP de `checkpoints*`; mezclar DSN SQLAlchemy con libpq.

## Impact
- backend: checkpointer wiring, deps, lifespan, tests, docs, posible ajuste Alembic `env.py`
- frontend: docs caveat only (opcional)

## Open questions
- ¿Flag `AGENTIC_CHECKPOINTER=memory|postgres` para demos offline sin Postgres? **Propuesta:** default postgres cuando hay `DATABASE_URL`; MemorySaver solo tests / flag explícito.
- ¿Incluir health check que verifique tablas checkpoint? **Propuesta:** no en v1; `setup()` al boot basta.

## Status
- [x] User approved — ready for OpenSpec propose
