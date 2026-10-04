# Draft: add-local-pgvector

## Surface
- Primary: **backend**
- Paths in this repo: `docker-compose.yml` (raíz), `backend/.env.example`, `backend/.env`, `backend/app/config.py`, `AGENTS.md` (cómo levantar)
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/` — servicio `vector-db` con imagen `pgvector/pgvector:pg16` en `docker-compose.yml`; `DATABASE_URL` en `ai-service/.env.example`
- Patterns borrowed (not copied):
  - Un Postgres **con extensión pgvector** como datastore del servicio IA (no Qdrant aparte)
  - Compose en la **raíz** del monorepo (evitar volumen con otro nombre de proyecto)
  - Credenciales vía env con defaults de desarrollo
  - Healthcheck `pg_isready`
  - Para desarrollo local con API en el host: **publicar** `5432` (el compose “prod” del curso no publica vector-db; el override `docker-compose.dev.yml` sí — nosotros arrancamos en modo dev desde el día 1)

## Intent
Levantar **Postgres + pgvector** local para el backend FastAPI, con `DATABASE_URL` en settings, de modo que el siguiente change de RAG pueda persistir chunks/embeddings sin inventar otra base.

No incluye aún tablas de corpus, Alembic ni endpoints de search/answer — solo infraestructura de DB lista y verificable.

## Non-goals
- Redis / CAG cache
- Segundo Postgres “de negocio” (Rails del curso) — no aplica
- Migraciones Alembic / tabla `chunks`
- Contenerizar el backend o el frontend
- Neon / Railway / producción
- Migrar el CRUD `items` a Postgres

## Draft requirements
- Existir `docker-compose.yml` en la raíz con un servicio Postgres basado en `pgvector/pgvector:pg16` (Postgres **16** + extensión pgvector de esa imagen; decisión explícita: alinear al curso `session_16`, no PG17/18).
- Incluir servicio **pgAdmin** en el mismo Compose (UI en host, p. ej. `5050`), dependiente de Postgres healthy.
- Volumen nombrado estable para no perder datos al recrear el contenedor.
- Puerto `5432` publicado en el host para que `uvicorn` en `backend/` se conecte a `localhost`.
- Healthcheck con `pg_isready`.
- Variables documentadas: usuario, password, db name; `DATABASE_URL` en formato SQLAlchemy/psycopg usable desde el host (`localhost:5432`).
- `backend/app/config.py` expone `database_url` (default local seguro para dev).
- `backend/.env.example` (y `.env` local) incluyen `DATABASE_URL`.
- `AGENTS.md` documenta `docker compose up -d` y cómo verificar.
- Tras el apply: contenedor healthy y conexión básica verificable (p. ej. `pg_isready` / `SELECT 1` o crear extensión `vector` una vez).

## Approach sketch
1. Añadir `docker-compose.yml` mínimo: servicio `vector-db` (nombre alineado al curso) o `postgres` — preferir un solo servicio claro, p. ej. `postgres` con imagen pgvector, DB `entrega_lidr`, user/password de dev.
2. Extender `Settings` con `database_url: str`.
3. Actualizar `.env.example` / `.env`; no commitear `.env`.
4. Dependencias Python de conexión (**no** en este change si no hay código que las use aún): opcional dejar nota; el apply puede añadir `psycopg[binary]` solo si se incluye un smoke script/check. Preferible: compose + settings ahora; driver en el change de persistence/RAG si no hay check.
5. Smoke al apply: `docker compose up -d`, esperar healthy, `docker compose exec … psql -c "CREATE EXTENSION IF NOT EXISTS vector;"` y `SELECT extname FROM pg_extension WHERE extname = 'vector';`.

Alineación a capas del curso: esto es **foundation/persistence** a nivel infra (compose + URL). Carpetas `foundation/persistence/` en Python quedan para el change siguiente (Alembic/models).

## Practices check (backend | both only)
- Aligned:
  - Settings vía `pydantic-settings` + `.env` / `.env.example`
  - No hardcodear secretos; defaults solo para local
  - Un datastore para el servicio IA (pgvector), sin frameworks paralelos
  - Documentar en `AGENTS.md` cómo correr
- Deviations (+ why):
  - Publicar `5432` en el compose de raíz (el curso lo oculta en el compose “completo” y lo abre en override de dev). **Por qué:** hoy la API corre en el host, no en compose; sin puerto no hay DB usable.
  - Aún no crear `foundation/persistence/` ni Alembic en este change. **Por qué:** alcance = levantar DB; el layout de capas entra con el primer modelo.
- Risks if ignored:
  - Sin `DATABASE_URL` en settings, el siguiente change de RAG inventa otra convención
  - Compose dentro de `backend/` renombra el proyecto/volumen y complica el monorepo (patrón del curso: compose en raíz)

## Impact
- backend: `config.py`, `.env.example`, docs de corrida; posiblemente `requirements.txt` si hay smoke con psycopg
- repo root: `docker-compose.yml`, mención en `AGENTS.md`
- frontend: ninguno

## Open questions
- Nombre del servicio/volumen: `postgres` vs `vector-db` — propuesta: servicio `postgres`, imagen pgvector, volumen `pgdata`, DB `entrega_lidr` (claridad en monorepo chico).
- ¿Habilitar extensión `vector` en un init script montado o solo documentar el `CREATE EXTENSION` manual en el apply? Propuesta: script `docker/init-vector.sql` montado en `docker-entrypoint-initdb.d` para que el primer arranque deje la extensión lista.

## Decisions
- **Postgres 16** via `pgvector/pgvector:pg16` (no 17/18). Motivo: misma línea que el curso; PG y pgvector van en la misma imagen, el tag `pg16` fija el major del motor.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-local-pgvector`
- Synced to `openspec/specs/local-pgvector/spec.md`
- Archived → `openspec/changes/archive/2026-09-30-add-local-pgvector/`
- Logged in `openspec/history.md`
