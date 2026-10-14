# Imagen del API FastAPI (Metropol RAG). || FastAPI API image (Metropol RAG).
#
# Railway construye desde este directorio (`backend/` como root directory),
# así que el contexto de build NO incluye `frontend/` ni `openspec/`.
#
# || Railway builds from this directory (`backend/` as the root directory),
# so the build context does NOT include `frontend/` or `openspec/`.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencias primero (capa estable). || Dependencies first (stable layer).
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Railway inyecta `PORT`. || Railway injects `PORT`.
ENV PORT=8000
EXPOSE 8000

# Migra y RECIÉN DESPUÉS sirve. Seguro con una sola instancia en Railway
# (misma premisa del activity log in-process). Si alembic falla, el contenedor
# no levanta y Railway no promueve el deploy.
#
# || Migrate then serve. Safe as a single Railway instance. `&&` matters:
# migration failure keeps the previous deploy. `sh -c` expands `$PORT`.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
