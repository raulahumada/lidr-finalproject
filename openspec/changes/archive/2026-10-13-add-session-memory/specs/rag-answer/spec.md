# rag-answer

## ADDED Requirements

### Requirement: Sync answer rejects session_id
`POST /api/v1/answer` is the single-shot path without conversation-memory framing before retrieve. It SHALL reject a request that includes `session_id` with HTTP 422 rather than accept the field and answer without memory.

#### Scenario: session_id on sync answer
- **WHEN** a client posts to `/answer` with a `session_id` field
- **THEN** the response is HTTP 422
- **AND** the body indicates that session memory is only available on agentic endpoints
- **AND** the service does not generate an answer for that request
