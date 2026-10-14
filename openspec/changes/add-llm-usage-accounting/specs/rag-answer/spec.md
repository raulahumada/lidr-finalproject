# Spec Delta: rag-answer

## MODIFIED Requirements

### Requirement: Answer endpoint accepts a question
The system SHALL expose `POST /api/v1/answer` that accepts a non-empty question and optional `k`, and returns an answer payload including text, citations, cache status, prompt version, latency, and a `usage` object with `input_tokens`, `output_tokens`, `total_tokens`, and `reported`. When generation runs, the active prompt version SHALL assemble retrieved evidence into discrete context blocks that expose a stable id and source path so citations can be verified. When generation ran, `usage` SHALL match the last completion for that request. When generation was skipped, `usage` SHALL be zeros with `reported=false`.

#### Scenario: Successful grounded answer
- **WHEN** embeddings and chat are configured and relevant chunks exist
- **AND** a client posts a question
- **THEN** the response includes a non-empty answer string
- **AND** citations reference retrieved sources when evidence was used
- **AND** `cached` indicates whether a response cache served the result
- **AND** `prompt_version` reflects the template version used for an uncached generation

#### Scenario: Context blocks carry provenance
- **WHEN** generation runs with one or more retrieved hits
- **THEN** the user prompt includes numbered (or otherwise discrete) blocks each showing a stable evidence id and source path

#### Scenario: Generated answer includes usage
- **WHEN** `POST /api/v1/answer` calls the model and the provider reports total 140 tokens
- **THEN** the HTTP 200 body includes `usage.total_tokens=140` and `usage.reported=true`

#### Scenario: No-evidence includes zero usage
- **WHEN** `POST /api/v1/answer` finds no evidence and skips the model
- **THEN** the body includes `usage` with zero token fields and `reported=false`

## ADDED Requirements

### Requirement: Sync answer usage reflects last completion only
When the sync answer path performs a chat completion, the response `usage` SHALL reflect that completion only. Ledger rows for the request are independent of whether Response CAG later serves a cached body on a different request.

#### Scenario: Cached semantic or exact hit reports unbilled zeros
- **WHEN** `POST /api/v1/answer` serves an exact or semantic cache hit without calling the model
- **THEN** the body `usage` has `reported=false` and zero token fields
- **AND** no new ledger row is written for that request
