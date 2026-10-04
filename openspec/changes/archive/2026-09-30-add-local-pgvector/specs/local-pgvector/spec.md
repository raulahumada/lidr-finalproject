# Spec Delta

## Purpose

Provides a local Postgres 16 database with the pgvector extension enabled, exposed for the FastAPI backend during development, plus a local pgAdmin UI to browse that database, so later RAG persistence can connect through a documented DATABASE_URL.

## ADDED Requirements

### Requirement: Local Postgres with pgvector image
The repository SHALL provide a Docker Compose service at the monorepo root that runs PostgreSQL **16** using the `pgvector/pgvector:pg16` image (or an equivalent tag that pins Postgres major version 16 with pgvector available).

#### Scenario: Compose defines the database service
- **WHEN** a developer inspects the root `docker-compose.yml`
- **THEN** there is a database service based on `pgvector/pgvector:pg16`
- **AND** it declares a named volume for data persistence
- **AND** it declares a healthcheck using `pg_isready`

### Requirement: Local pgAdmin UI
The Compose stack SHALL include a pgAdmin service that depends on the database being healthy, publishes a HTTP port on the host (default `5050`), and can register/connect to the Compose Postgres service over the internal Docker network.

#### Scenario: pgAdmin is reachable after bring-up
- **WHEN** the Compose stack is up and the database is healthy
- **THEN** a developer can open the documented pgAdmin URL on localhost
- **AND** log in with the documented local credentials
- **AND** connect to the project database (host = Compose service name of Postgres, not `localhost` from inside pgAdmin’s container)

### Requirement: Host port for local API
The database service SHALL publish port `5432` on the host so a backend process running outside Compose can connect via `localhost`.

#### Scenario: Port is reachable from the host
- **WHEN** the Compose stack is up and healthy
- **THEN** a client on the host can connect to Postgres on `localhost:5432` with the documented credentials

### Requirement: Vector extension on first init
On first database initialization, the system SHALL enable the `vector` extension so pgvector types are available without a manual one-off step.

#### Scenario: Extension exists after first start
- **WHEN** the database volume is created for the first time and the service becomes healthy
- **THEN** querying `pg_extension` for `vector` returns a row
- **AND** recreating only the container (keeping the volume) does not require re-running init scripts to keep the extension

### Requirement: Connection settings for the backend
The backend settings SHALL expose a `database_url` (env `DATABASE_URL`) suitable for connecting from the host to the Compose database, and `.env.example` SHALL document that value.

#### Scenario: Settings expose DATABASE_URL
- **WHEN** a developer reads `backend/.env.example` and `Settings`
- **THEN** `DATABASE_URL` / `database_url` is documented with a localhost default matching the Compose credentials and database name
- **AND** the `.env` file with secrets remains untracked

### Requirement: Documented start and verify
Project agent/ops documentation SHALL describe how to start the database with Compose and how to verify health and the `vector` extension.

#### Scenario: AGENTS documents the workflow
- **WHEN** a developer follows `AGENTS.md`
- **THEN** they can run Compose for the database and verify the service is healthy and `vector` is installed
- **AND** they can open pgAdmin using the documented URL and login
