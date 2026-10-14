# Spec Delta: llm-usage-accounting

## Purpose

Captures provider-reported chat token usage for Metropol answer paths, persists a durable ledger of successful completions, exposes last-completion usage on answer HTTP payloads, and aggregates spend for operators via a summary endpoint.

## ADDED Requirements

### Requirement: Chat completions expose provider-reported usage
A successful chat completion used by answer paths SHALL yield a usage value with `input_tokens`, `output_tokens`, `total_tokens`, and `reported`. When the provider returns OpenAI-compatible `usage`, those fields SHALL be copied (`prompt_tokens` → input, `completion_tokens` → output, `total_tokens` → total) and `reported` SHALL be true. Callers SHALL obtain usage without reading vendor SDK objects directly.

#### Scenario: OpenAI usage is copied
- **WHEN** a chat completion returns usage with prompt 100, completion 40, and total 140
- **THEN** usage is `input_tokens=100`, `output_tokens=40`, `total_tokens=140`, `reported=true`

### Requirement: Missing provider usage is marked, not invented
If the provider omits `usage` or required token fields, the system SHALL return zeros with `reported=false` and SHALL emit a warning. It SHALL NOT fail the completion and SHALL NOT invent tokens from character counts or local tokenizers.

#### Scenario: Response without usage still returns content
- **WHEN** a provider returns assistant content and no usage block
- **THEN** the completion content is still returned
- **AND** usage has `reported=false` and zero token fields

### Requirement: Each successful HTTP answer completion persists one ledger row
A successful chat completion on an HTTP answer path SHALL insert one row into the usage ledger with `purpose` (`answer`, `grounded_composer`, or `prompt_specialist`), `model`, the three token fields, `reported`, and nullable `session_id`, `thread_id`, and `owner_id` (from `X-Console-User` when present). The insert SHALL happen at call time, not when the conversation turn closes. A later human-review reject SHALL NOT delete the row. A failed provider call SHALL NOT insert a row.

#### Scenario: Sync answer writes one row when the model is called
- **WHEN** `POST /api/v1/answer` performs a chat completion with reported usage
- **THEN** the ledger gains one row with `purpose="answer"` and those token counts
- **AND** `session_id` and `thread_id` are null

#### Scenario: Second composition after adjust is a second row
- **WHEN** an agentic run completes grounded composition, pauses at the human gate, and resumes with `adjust` so composition runs again
- **THEN** two ledger rows exist with `purpose="grounded_composer"` and the same `thread_id`

### Requirement: Skipped completions do not write ledger rows
When the answer path returns without calling the model (including no-evidence, empty fitted context, or a Response CAG hit that skips generation), the system SHALL NOT insert a ledger row.

#### Scenario: No-evidence writes no event
- **WHEN** `POST /api/v1/answer` finds no evidence and does not call the model
- **THEN** the ledger gains no row for that request

### Requirement: Ledger write failure does not fail the answer
If inserting a ledger row raises, the system SHALL log a failure event and SHALL still return the answer to the caller.

#### Scenario: Store outage still returns the answer
- **WHEN** a successful completion is followed by a failed ledger insert
- **THEN** the caller still receives the answer payload
- **AND** a ledger-failure warning is logged

### Requirement: GET usage summary returns aggregates
The system SHALL expose `GET /api/v1/usage/summary` returning `total_calls` and the three token sums, plus a `by_model` list of `{model, calls, input_tokens, output_tokens, total_tokens}` (provider id optional). Optional query filters `from`, `to`, `session_id`, and `purpose` SHALL narrow the aggregate. `from` later than `to` SHALL be HTTP 422. An empty window SHALL return zeros and an empty `by_model`, not an error. The summary SHALL NOT accept a tenant id query parameter.

#### Scenario: Summary after two calls to the same model
- **WHEN** the ledger has two reported rows for the same model totaling 200 input and 80 output
- **THEN** `GET /api/v1/usage/summary` returns `total_calls=2`, `input_tokens=200`, `output_tokens=80`, `total_tokens=280`
- **AND** `by_model` has one entry for that model with the same counts

#### Scenario: Inverted time range is rejected
- **WHEN** `GET /api/v1/usage/summary` is called with `from` later than `to`
- **THEN** the response is HTTP 422
