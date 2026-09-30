# Tasks

## 1. Compose + init

- [x] 1.1 Add root `docker-compose.yml` with service `postgres`, image `pgvector/pgvector:pg16`, env for user/password/db `entrega_lidr`, volume `pgdata`, ports `5432:5432`, healthcheck `pg_isready` — verify file parses with `docker compose config`
- [x] 1.2 Add `docker/init-vector.sql` with `CREATE EXTENSION IF NOT EXISTS vector;` mounted into `docker-entrypoint-initdb.d` — verify the mount path appears in `docker compose config`
- [x] 1.3 Add Compose service `pgadmin` (`dpage/pgadmin4`), depends on `postgres` healthy, publish `5050:80`, env for default email/password, and document connection host `postgres` — verify `docker compose config` lists `pgadmin` and port `5050`

## 2. Backend settings

- [x] 2.1 Add `database_url` to `Settings` in `backend/app/config.py` with a localhost default matching Compose credentials — verify `get_settings().database_url` is non-empty when imported from `backend/`
- [x] 2.2 Update `backend/.env.example` with `DATABASE_URL` and sync local `backend/.env` (do not commit `.env`) — verify `.env.example` contains the key and `.env` is gitignored

## 3. Docs + bring-up

- [x] 3.1 Document in `AGENTS.md` how to run `docker compose up -d`, wait for healthy, verify the `vector` extension, and open pgAdmin (`http://localhost:5050` + login + server host `postgres`) — verify the commands/URLs in the doc match Compose
- [x] 3.2 Run `docker compose up -d`, wait until healthy, confirm `vector` via `psql`, and confirm pgAdmin responds on port `5050` — verify `pg_isready` succeeds, extension query returns `vector`, and `http://localhost:5050` is reachable

- [x] 3.3 Mark draft `openspec/drafts/add-local-pgvector.md` Status as approved/promoted to this change — verify the Status checkbox or promotion line is present
