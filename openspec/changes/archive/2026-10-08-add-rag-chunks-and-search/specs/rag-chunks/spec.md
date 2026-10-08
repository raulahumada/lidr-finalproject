# rag-chunks

## Purpose

Persists corpus documents and their text chunks with optional vector embeddings in the local Postgres+pgvector database, via versioned schema migrations, so later retrieval and Metropol Fintech ingestion have a stable store.

## ADDED Requirements

### Requirement: Versioned schema for documents and chunks
The backend SHALL provide Alembic migrations that create a `documents` table and a `chunks` table suitable for RAG persistence, and SHALL ensure the Postgres `vector` extension is available before any vector column is created.

#### Scenario: Migration creates store tables
- **WHEN** a developer runs the documented Alembic upgrade against the local Compose database
- **THEN** tables `documents` and `chunks` exist
- **AND** `chunks` has a nullable embedding column of dimension 1536 using the pgvector type
- **AND** each chunk references a document with cascade delete
- **AND** querying `pg_extension` for `vector` returns a row

#### Scenario: Relational indexes without vector index
- **WHEN** the initial RAG schema migration is applied
- **THEN** basic relational indexes exist for document lookup and chunk foreign keys
- **AND** no HNSW or IVFFlat vector index is required yet

### Requirement: Application can connect and map store rows
The backend SHALL expose a persistence layer that connects using `DATABASE_URL` from settings and can read/write document and chunk rows (including embeddings) without placing SQL in HTTP routers.

#### Scenario: Settings drive the database URL
- **WHEN** `DATABASE_URL` is set in the backend environment
- **THEN** the persistence layer uses that URL for connections
- **AND** secrets are not hardcoded in source

### Requirement: Local fixture seed without client corpus
The system SHALL provide a documented CLI (or equivalent non-UI) seed that inserts at least one fixture document with one or more chunks and embeddings, so search can be exercised without the Metropol Fintech corpus path.

#### Scenario: Seed populates searchable chunks
- **WHEN** a developer runs the documented seed with a valid embeddings API key and a migrated database
- **THEN** at least one document and one chunk with a non-null embedding exist
- **AND** the seed does not require client corpus files outside the repo fixture
