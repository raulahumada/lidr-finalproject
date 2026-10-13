# Spec Delta: corpus-ingest

## ADDED Requirements

### Requirement: HTTP start of corpus ingest run
The backend SHALL expose `POST /api/v1/ingest/runs` that accepts an optional `force` flag, starts an ingest of the configured `CORPUS_ROOT` using the same ingest semantics as the CLI (allowlist, skip/force by source path, embeddings), and returns HTTP 202 with a `run_id` and an initial status of `queued` or `running`. The request SHALL NOT accept a client-supplied corpus root path.

#### Scenario: Successful start
- **WHEN** `CORPUS_ROOT`, embeddings, and database settings are configured
- **AND** no other ingest run is currently running
- **AND** a client calls `POST /api/v1/ingest/runs` with optional `force`
- **THEN** the response status is 202
- **AND** the body includes a non-empty `run_id` and status `queued` or `running`

#### Scenario: Missing configuration
- **WHEN** `CORPUS_ROOT`, embeddings, or database settings are not configured for ingest
- **AND** a client calls `POST /api/v1/ingest/runs`
- **THEN** the response status is 503 with a clear error detail

#### Scenario: Concurrent run rejected
- **WHEN** an ingest run is already `queued` or `running`
- **AND** a client calls `POST /api/v1/ingest/runs` again
- **THEN** the response status is 409

### Requirement: HTTP poll of ingest run status
The backend SHALL expose `GET /api/v1/ingest/runs/{run_id}` that returns the run status (`queued`, `running`, `completed`, or `failed`). When the run has finished successfully, the response SHALL include summary counts compatible with the CLI summary (seen, ingested, skipped by extension, skipped existing, failed, chunks) and a truncated list of per-file errors when any exist. Unknown `run_id` SHALL return 404.

#### Scenario: Completed run returns summary
- **WHEN** a previously started run has completed successfully
- **AND** a client polls `GET /api/v1/ingest/runs/{run_id}`
- **THEN** status is `completed`
- **AND** summary counts are present

#### Scenario: Unknown run
- **WHEN** a client polls a `run_id` that is not known to the server
- **THEN** the response status is 404

### Requirement: HTTP corpus stats without starting a run
The backend SHALL expose `GET /api/v1/ingest/stats` that returns current document and chunk counts from the RAG store plus the configured corpus root path string and extension allowlist, without starting an ingest run.

#### Scenario: Stats when index is empty
- **WHEN** the RAG store has zero documents
- **AND** a client calls `GET /api/v1/ingest/stats`
- **THEN** document and chunk counts are zero
- **AND** the configured corpus root and allowlist are still returned when settings define them
