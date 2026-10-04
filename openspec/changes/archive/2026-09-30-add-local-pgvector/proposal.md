# Proposal

## Why

El backend FastAPI aún no tiene datastore local. Sin Postgres + pgvector no se puede persistir el corpus RAG (chunks/embeddings) ni alinear el servicio IA al layout del curso. Ahora hace falta la base lista y documentada antes del pipeline de indexación.

## What Changes

- Añadir `docker-compose.yml` en la raíz con Postgres **16** vía imagen `pgvector/pgvector:pg16`, volumen persistente, healthcheck y puerto `5432` publicado al host.
- Añadir servicio **pgAdmin** en el mismo Compose (UI web local, p. ej. puerto `5050`) conectado a ese Postgres.
- Inicializar la extensión `vector` en el primer arranque (`docker/init-vector.sql`).
- Exponer `database_url` en `backend/app/config.py` (settings) y documentarla en `backend/.env.example` (y `.env` local).
- Documentar en `AGENTS.md` cómo levantar DB + pgAdmin y verificar.
- **No** incluye Alembic, tabla `chunks`, drivers de app obligatorios, Redis, ni endpoints RAG.

## Capabilities

### New Capabilities
- `local-pgvector`: Postgres 16 + extensión pgvector local vía Docker Compose, pgAdmin para administración visual, URL de conexión en settings del backend, y arranque/verificación documentados para desarrollo.

### Modified Capabilities
- (ninguna)

## Impact

- **Surface:** backend (+ infra en raíz del monorepo).
- **Paths:** `docker-compose.yml`, `docker/init-vector.sql`, `backend/app/config.py`, `backend/.env.example`, `backend/.env` (local, no commit), `AGENTS.md`.
- **APIs:** sin cambios de contrato HTTP.
- **Deps:** sin dependencia Python obligatoria en este change (conexión de app llega con persistence/RAG).
- **Course ref:** patrón `vector-db` / `pgvector/pgvector:pg16` de `session_16`; puerto publicado como en el override de desarrollo del curso.

## Practices check

- **Aligned:**
  - Settings vía `pydantic-settings` + `.env` / `.env.example`
  - Secretos/credenciales por env; defaults solo para local
  - Un datastore para el servicio IA (pgvector), sin store paralelo inventado
  - Documentación operativa en `AGENTS.md`
- **Deviations:**
  - Publicar `5432` en el compose de raíz (el compose “estricto” del curso no publica la DB; el override de dev sí). Motivo: la API corre en el host hoy.
  - No crear aún `foundation/persistence/` ni Alembic. Motivo: alcance = infra DB; capas Python en el change de modelos.
- **Risks if ignored:**
  - Sin `DATABASE_URL` convencional, el change de RAG inventa otra forma de conexión
  - Compose dentro de `backend/` renombra el proyecto Docker y el volumen
