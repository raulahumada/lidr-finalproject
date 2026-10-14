# Puesta en marcha local (paso a paso)

Objetivo: consola en `http://localhost:3000` hablando con FastAPI en `http://localhost:8000`, con Postgres (RAG + auth) y Redis.

Asume **macOS + bash/zsh**. Todos los paths son relativos a la raíz del monorepo salvo que diga lo contrario.

## 0. Prerrequisitos

- Docker Desktop
- Python 3.12+
- Node 20+
- Cuenta OpenAI (`OPENAI_API_KEY`)
- Carpeta local del corpus Metropol (opcional al inicio; necesaria para ingest real)

## 1. Infra local (Compose)

```bash
cp .env.example .env
# Editar POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, PGADMIN_*
docker compose up -d
docker compose ps   # postgres + redis healthy
```

Verificar extensión `vector`:

```bash
set -a && source .env && set +a
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

Crear la DB de identidad (Auth.js / Prisma):

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" \
  -c "CREATE DATABASE entrega_lidr_auth;"
```

(Si el nombre de la auth DB en tu `frontend/.env.local` es otro, usá ese.)

pgAdmin (opcional): `http://localhost:5050` — host del server = `postgres` (nombre del servicio), no `localhost`.

## 2. Backend

```bash
cd backend
cp .env.example .env
```

Alinear:

- `DATABASE_URL=postgresql+psycopg://USER:PASS@localhost:5432/DB` (mismos USER/PASS/DB del root `.env`)
- `OPENAI_API_KEY=…`
- `REDIS_URL=redis://localhost:6379`
- `CORPUS_ROOT=` ruta absoluta al corpus (cuando vayas a ingerir)
- `SERVICE_TOKEN=` vacío en local (API abierta) **o** el mismo valor que pondrás en `frontend/.env.local`

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Smoke:

```bash
curl -s http://localhost:8000/api/v1/health
# {"status":"ok"} o similar
```

## 3. Frontend

```bash
cd frontend
cp .env.example .env.local
```

Alinear:

- `AUTH_DATABASE_URL=postgresql://USER:PASS@localhost:5432/entrega_lidr_auth`
- `AI_SERVICE_URL=http://localhost:8000`
- `AUTH_SECRET=` (`openssl rand -base64 32`)
- `SERVICE_TOKEN=` igual que backend (o vacío si backend abierto)

```bash
npm install
npm run db:migrate
npm run seed:admin -- admin@example.com
# o: AUTH_SEED_PASSWORD='…' npm run seed:admin -- admin@example.com
npm run dev
```

Abrí `http://localhost:3000/login`. El registro crea usuarios **disabled** hasta que un admin los habilite en `/users`.

## 4. Ingest corpus (local)

Con API o solo CLI (CLI no necesita Uvicorn):

```bash
cd backend && source .venv/bin/activate
# CORPUS_ROOT y OPENAI_API_KEY en .env
python -m app.ingestion.run_ingest
```

Smoke search:

```bash
curl -s http://localhost:8000/api/v1/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"cobranzas handoff","k":5}' | python3 -m json.tool
```

Si `SERVICE_TOKEN` está seteado, agregá `-H "Authorization: Bearer $SERVICE_TOKEN"`.

## 5. Chat agentic desde la consola

1. Login como admin.
2. `/answer` → nueva sesión → pregunta de dominio Metropol.
3. Si el gate pausa (`awaiting_human_review`), aprobá/rechazá/ajustá en la UI.

## 6. Apagar

```bash
docker compose down       # conserva volúmenes
docker compose down -v    # borra datos Postgres/Redis
```

## Siguiente: producción

Ver [`deploy-railway-vercel.md`](deploy-railway-vercel.md).
