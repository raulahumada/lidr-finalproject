# corpus-ingest

## Purpose

Ingests Metropol Fintech corpus files from a configured local directory into the existing RAG document/chunk store with embeddings, so semantic search can retrieve real client knowledge instead of only demo fixtures.

## ADDED Requirements

### Requirement: Configurable corpus root and extension allowlist
The backend SHALL read a `CORPUS_ROOT` path and an extension allowlist from settings (defaults covering pdf, docx, txt, and md), and SHALL document those settings in `.env.example` without embedding a machine-specific path in source code.

#### Scenario: Settings expose corpus configuration
- **WHEN** a developer inspects settings and `.env.example`
- **THEN** `CORPUS_ROOT` and the allowlist are documented
- **AND** missing `CORPUS_ROOT` prevents a successful ingest run with a clear error

### Requirement: Filesystem walk with skip of unsupported types
The ingest run SHALL recursively walk `CORPUS_ROOT`, attempt parse+persist only for allowlisted extensions, and skip other files while counting them in the run summary (no hard failure solely because unsupported files exist).

#### Scenario: Unsupported extensions are skipped
- **WHEN** the corpus contains files such as mp4, png, or xlsx alongside allowlisted docs
- **AND** an ingest run executes
- **THEN** allowlisted files may be ingested
- **AND** unsupported files are skipped and reflected in the summary counts

### Requirement: Parse, chunk, embed, and persist
For each ingested file, the system SHALL extract text via a format-specific parser, split into chunks, embed with the same embedding model used by search, and persist document + chunks into the existing RAG tables.

#### Scenario: Successful ingest of a text file
- **WHEN** `CORPUS_ROOT` contains an allowlisted file with extractable text and embeddings are configured
- **AND** an ingest run processes that file
- **THEN** a document row exists for that source path
- **AND** one or more chunks with non-null embeddings exist for that document

### Requirement: Idempotent by source path
Re-running ingest SHALL NOT duplicate the same `source_path` by default (skip). A documented force mode SHALL allow replacing an already-ingested document (cascade delete chunks and re-load).

#### Scenario: Second run skips existing path
- **WHEN** a source path was already ingested
- **AND** ingest runs again without force
- **THEN** that path is not duplicated as a second document

#### Scenario: Force re-ingests existing path
- **WHEN** a source path was already ingested
- **AND** ingest runs with force enabled for that path
- **THEN** the previous document for that path is replaced and chunks are refreshed

### Requirement: Documented CLI entrypoint
The repository SHALL provide a documented CLI module to run ingest from `backend/`, printing a summary of seen / ingested / skipped / failed files and chunk counts.

#### Scenario: Operator can run ingest from docs
- **WHEN** a developer follows `AGENTS.md` with Compose DB up, migrations applied, `CORPUS_ROOT` and `OPENAI_API_KEY` set
- **THEN** they can run the documented command and obtain a run summary
