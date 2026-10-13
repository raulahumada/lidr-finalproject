# agentic-answer

## ADDED Requirements

### Requirement: Agentic outcomes expose resolved_question when rewritten
When conversation resolution rewrites the written question for retrieval, agentic completed/paused/rejected payloads SHALL include `resolved_question` with that resolved text. When no rewrite occurred, `resolved_question` MAY be null or omitted.

#### Scenario: Rewrite present on payload
- **WHEN** an agentic run bound to a session rewrites a referential follow-up
- **THEN** the response includes a `resolved_question` distinct from the written question
