# Entrega LiDR — guía para agentes

Monorepo en etapa inicial. Dos apps independientes: API FastAPI y frontend Next.js. Integración frontend↔backend aún no cableada del todo.

**Producto:** plataforma **multiagente + RAG** para el Máster AI Engineering (LIDR), con cliente **Metropol Fintech**. El corpus RAG es la documentación de omnicanalidad/agentes del cliente (también en NotebookLM). Visión, dominio y agentes: **`README.md`**. Este archivo es solo guía operativa del código.

## Estructura

```
entrega-lidr/
├── AGENTS.MD          ← este archivo (contexto de repo)
├── docker-compose.yml ← Postgres 16 + pgvector + pgAdmin (local)
├── docker/            ← init SQL (extensión vector)
├── backend/           ← FastAPI ("Entrega LiDR API")
└── frontend/          ← Next.js 16 + React 19 ("lidr-front")
    └── AGENTS.md      ← reglas Next.js (canary) + Astryx; no duplicar aquí
```

## Base de datos local (Postgres + pgvector + pgAdmin)

Credenciales en la **raíz**: copiá `.env.example` → `.env` y reemplazá los placeholders. Compose lee ese `.env` solo; no van passwords en `docker-compose.yml`.

```bash
cp .env.example .env   # editar POSTGRES_* y PGADMIN_*
docker compose up -d
docker compose ps   # postgres healthy
```

Verificar extensión `vector` (user/db = valores de tu `.env`):

```bash
# macOS / zsh o bash: cargá vars del .env de la raíz si hace falta
set -a && source .env && set +a
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Si preferís literales: `docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB> -c "SELECT …"` con los valores de tu `.env`.

Scripts de agentes (prespec, etc.) asumen **bash en macOS**; no dependen de PowerShell.

- **API / tools en el host:** `DATABASE_URL` en `backend/.env` (plantilla `backend/.env.example`); debe usar el mismo user/password/db que el Compose root `.env`.
- **pgAdmin:** http://localhost:5050 — login = `PGADMIN_DEFAULT_EMAIL` / `PGADMIN_DEFAULT_PASSWORD` de tu `.env`.
  - Al registrar el server: Host = `postgres` (nombre del servicio Compose), Port `5432`, DB/User/Password = `POSTGRES_*` del `.env`.
  - No uses `localhost` como host *desde dentro* de pgAdmin: ese hostname es el contenedor de pgAdmin, no Postgres.

```bash
docker compose down      # para contenedores; conserva volumen pgdata
docker compose down -v   # además borra datos
```

## Backend (`backend/`)

Stack: FastAPI, Uvicorn, Pydantic Settings, python-dotenv.

| Path | Rol |
|------|-----|
| `app/main.py` | Factory `create_app()`, CORS, monta router |
| `app/config.py` | Settings desde `.env` (`get_settings()` cacheado), incluye `database_url` + embeddings |
| `app/dependencies.py` | Composition root (retriever, etc.) |
| `app/api/router.py` | Agrega routers de rutas |
| `app/api/routes/health.py` | `GET /api/v1/health` |
| `app/api/routes/items.py` | CRUD `/api/v1/items` en memoria |
| `app/api/routes/search.py` | `POST /api/v1/search` (semántico sobre chunks) |
| `app/foundation/persistence/` | SQLAlchemy engine, modelos `documents`/`chunks`, store |
| `app/generation/rag/` | Embedder OpenAI, retriever, seed fixture |
| `app/schemas/` | Contratos Pydantic (items, search) |
| `alembic/` | Migraciones (pgvector chunks) |
| `.env.example` | Plantilla de env |

API prefix por defecto: `/api/v1`. Docs: `/docs`.

CORS por defecto: `http://localhost:3000`, `http://localhost:5173`.

**Python:** 3.10+ (recomendado 3.12 vía Homebrew). Crear venv: `cd backend && python3.12 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.

**Items:** store en memoria (`dict`); se pierde al reiniciar.

**RAG (chunks + search):** tablas `documents` / `chunks` vía Alembic; embeddings `text-embedding-3-small` (1536-d). Sin `OPENAI_API_KEY`, search responde **503**. Corpus vacío → **200** con `results: []`.

### Correr backend

```bash
cd backend
cp .env.example .env   # si hace falta; alinear DATABASE_URL con root Compose
# editar OPENAI_API_KEY=
source .venv/bin/activate   # o: python3.12 -m venv .venv && …
uvicorn app.main:app --reload
```

Dependencias: `requirements.txt`.

### Migraciones + seed + search (macOS / bash)

Con Postgres Compose healthy:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
python -m app.generation.rag.seed_fixture   # requiere OPENAI_API_KEY
```

Ejemplo de búsqueda:

```bash
curl -s http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"cobranzas handoff","k":5}' | python3 -m json.tool
```

Tests: `cd backend && .venv/bin/python -m pytest -q`.

## Frontend (`frontend/`)

Stack: Next.js `16.3.5` (App Router), React `19.2.8`, TypeScript, Tailwind CSS 4, ESLint.

UI kit instalado pero **aún no integrado** en el código de app:

- `@astryxdesign/core` + `@astryxdesign/theme-neutral` `^0.6.1`
- CLI: `@astryxdesign/cli` → `npx astryx <cmd>`

La home (`app/page.tsx`) y el layout siguen siendo el boilerplate de `create-next-app` (Geist, Tailwind crudo). Falta importar CSS de Astryx y migrar UI a componentes del kit.

Detalle operativo de Next + Astryx: leer **`frontend/AGENTS.md`** antes de tocar UI.

### Correr frontend

```bash
cd frontend
npm install   # si hace falta
npm run dev   # http://localhost:3000
```

Scripts: `dev`, `build`, `start`, `lint`.

## Estado actual / gaps

- Sin package/workspace root; cada carpeta se instala y corre por separado.
- RAG mínimo: Alembic + `POST /api/v1/search` + seed fixture; falta corpus Metropol real, `/answer` y agentes.
- Items CRUD sigue en memoria.
- Sin cliente HTTP ni tipos compartidos entre front y back.
- Astryx en `package.json` pero no cableado en `layout.tsx` / `globals.css`.
- Metadata del front aún dice "Create Next App".

## Convenciones para agentes

1. Cambios de API → `backend/`; UI → `frontend/`. No inventar carpetas compartidas sin pedirlo.
2. Antes de UI nueva: seguir el workflow de Astryx en `frontend/AGENTS.md` (`astryx build`, templates, components). No inventar layout con `<div>` + CSS a mano.
3. Next.js 16 puede diferir del entrenamiento: consultar docs bajo `frontend/node_modules/next/dist/docs/` cuando haga falta.
4. No commitear `.env` del backend; usar `.env.example` como referencia.
5. Preferir extender el CRUD de items / health existentes antes de crear routers o stores paralelos, salvo que el usuario pida otra cosa.
6. Documentación de agente de producto vive aquí; reglas específicas de front viven en `frontend/AGENTS.md`.
7. Cambios alineados a la arquitectura del curso: `/opsx-prespec` (draft + sync referencia + surface front|back|both → OpenSpec propose). Implementar con `/opsx-apply`.
8. Backend Python: seguir y contrastar `docs/python-best-practices.md` en `/opsx-propose` y `/opsx-prespec` (sección Practices check).
