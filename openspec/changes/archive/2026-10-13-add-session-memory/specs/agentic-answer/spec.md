# agentic-answer

## ADDED Requirements

### Requirement: Session hydrates a conversation window for framing
When agentic submit includes a valid `session_id`, the run SHALL load a sliding window of the most recent closed history turns (count bounded by configuration, default 4) into graph state before framing and retrieval. An unknown `session_id` continues to yield HTTP 404 before the graph starts.

#### Scenario: Window loaded for known session
- **WHEN** `POST /answer/agentic` or `/answer/agentic/start` includes a known `session_id` with prior closed turns
- **THEN** framing and retrieval run with access to that recent window

#### Scenario: Empty session window
- **WHEN** the session exists but has no closed turns yet
- **THEN** the run proceeds with an empty window and no referential rewrite

### Requirement: Framing uses resolved question for retrieve
The intent-framing step SHALL set the framed query used by corpus fetch to the resolved question from conversation-memory rules when a window is present; otherwise it SHALL pass through the written question.

#### Scenario: Retrieve uses resolved text
- **WHEN** resolution rewrites a referential follow-up
- **THEN** corpus fetch queries with the resolved text, not only the raw follow-up

## MODIFIED Requirements

### Requirement: Terminal outcomes append session history
When a run bound to a `session_id` reaches a terminal operator-facing outcome (`completed`, `rejected`, or completed after `adjust`), the system SHALL append a history turn with question, answer (if any), citation snapshots, status, and `thread_id`. When resolution rewrote the question, the turn SHALL also store `resolved_question`. The system SHALL NOT append while status is `running` or `awaiting_human_review`. If the session has no title, the system MAY set title from a truncation of the first question.

#### Scenario: Append after approve resume
- **WHEN** a paused run with `session_id` is resumed with approve and completes
- **THEN** the session history includes that turn with status completed

#### Scenario: Append after reject
- **WHEN** a paused run with `session_id` is resumed with reject
- **THEN** the session history includes a turn marked rejected

#### Scenario: No append on pause
- **WHEN** a run with `session_id` pauses at awaiting_human_review
- **THEN** history is unchanged until a terminal resume or other terminal outcome

#### Scenario: Append stores resolved question when rewritten
- **WHEN** a terminal turn was framed with a resolved question different from the written question
- **THEN** the appended history turn includes that `resolved_question`
