# agentic-answer

## ADDED Requirements

### Requirement: Optional session_id binds a run to a conversation
Agentic submit endpoints SHALL accept an optional `session_id`. When present and valid, the run is associated with that conversation for transcript append rules. When absent, behavior remains as today (no session transcript). An unknown `session_id` SHALL yield HTTP 404 before the graph is started.

#### Scenario: Valid session on sync agentic
- **WHEN** `POST /answer/agentic` includes a known `session_id` and the run completes without pause
- **THEN** the session history gains a closed turn for that question and answer

#### Scenario: Unknown session rejected
- **WHEN** agentic submit includes a `session_id` that does not exist
- **THEN** the API responds HTTP 404 and does not start the graph

### Requirement: Terminal outcomes append session history
When a run bound to a `session_id` reaches a terminal operator-facing outcome (`completed`, `rejected`, or completed after `adjust`), the system SHALL append a history turn with question, answer (if any), citation snapshots, status, and `thread_id`. The system SHALL NOT append while status is `running` or `awaiting_human_review`. If the session has no title, the system MAY set title from a truncation of the first question.

#### Scenario: Append after approve resume
- **WHEN** a paused run with `session_id` is resumed with approve and completes
- **THEN** the session history includes that turn with status completed

#### Scenario: Append after reject
- **WHEN** a paused run with `session_id` is resumed with reject
- **THEN** the session history includes a turn marked rejected

#### Scenario: No append on pause
- **WHEN** a run with `session_id` pauses at awaiting_human_review
- **THEN** history is unchanged until a terminal resume or other terminal outcome
