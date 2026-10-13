# chat-sessions

## MODIFIED Requirements

### Requirement: Read session returns durable history
The system SHALL expose `GET /api/v1/answer/session/{session_id}` that returns the session view including `history` turns (question, optional `resolved_question`, answer, citation snapshots, terminal status, related `thread_id` when known, timestamp).

#### Scenario: Unknown session
- **WHEN** the session id was never minted or was deleted
- **THEN** the API responds HTTP 404

#### Scenario: History after turns
- **WHEN** the session has closed turns
- **THEN** `history` lists those turns in chronological order

#### Scenario: Resolved question on turn
- **WHEN** a closed turn was stored with a rewritten query
- **THEN** that history entry includes `resolved_question`
