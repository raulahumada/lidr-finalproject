# agentic-live-progress Specification

## Purpose
Provides background execution of the Metropol agentic answer graph with narrated per-node activity and a pollable progress endpoint so clients can show live specialist steps without waiting for a blocking invoke.

## Requirements

### Requirement: Start schedules a background agentic run
The system SHALL expose `POST /api/v1/answer/agentic/start` that accepts a non-empty question, optional `k`, and optional `session_id`, schedules the agentic graph in the background, and returns HTTP 202 with status `running` and a `thread_id` without waiting for the graph to finish. When `session_id` is provided, session binding and terminal append rules from `agentic-answer` / `chat-sessions` SHALL apply.

#### Scenario: Start returns immediately
- **WHEN** a valid question is posted to `/answer/agentic/start` and generation is configured
- **THEN** the response is HTTP 202 with status `running` and a non-empty `thread_id`

#### Scenario: Missing API key
- **WHEN** the OpenAI API key is not configured
- **THEN** `/answer/agentic/start` responds with HTTP 503

#### Scenario: Start with session
- **WHEN** start includes a known `session_id`
- **THEN** the run is associated with that session for later history append on terminal outcomes

### Requirement: Progress reports activity while running
The system SHALL expose `GET /api/v1/answer/agentic/{thread_id}/progress` that returns the narrated activity accumulated so far. While the run is in progress, status SHALL be `running` and the payload SHALL include an `activity` list without inventing a final answer.

#### Scenario: Poll while running
- **WHEN** a client polls `/progress` for a started thread before the graph reaches a terminal state
- **THEN** the response has status `running` and an `activity` list of zero or more narrated node entries

### Requirement: Progress reports terminal results
When a background run completes, pauses for human review, or fails, `/progress` SHALL report status `completed`, `awaiting_human_review`, or `failed` respectively, and SHALL include the corresponding answer payload fields or error without leaving the thread stuck at `running`.

#### Scenario: Completed run
- **WHEN** the background graph finishes without escalation
- **THEN** `/progress` returns status `completed` with answer and citations consistent with sync agentic rules

#### Scenario: Human pause
- **WHEN** the escalation gate pauses the run
- **THEN** `/progress` returns status `awaiting_human_review` with `thread_id`, `review_reasons`, and `activity`

#### Scenario: Background failure
- **WHEN** the background task raises before a terminal graph state
- **THEN** `/progress` returns status `failed` with an error message

### Requirement: Unknown progress thread is 404
The system SHALL respond HTTP 404 when `/progress` is called with a `thread_id` that was never started (or is unknown to the activity log).

#### Scenario: Unknown thread
- **WHEN** a client polls `/progress` for an unknown `thread_id`
- **THEN** the response is HTTP 404

### Requirement: Activity narrates Metropol specialist nodes
While streaming graph updates, the system SHALL append human-readable activity entries for specialist nodes that execute (intent framing, corpus fetch, grounded composition, source guard, escalation gate), degrading unrecognized shapes to a generic line instead of failing the run.

#### Scenario: Traceable activity on completion
- **WHEN** a background run reaches a terminal status
- **THEN** `activity` includes ordered entries covering specialist steps that executed

### Requirement: Chat UI uses start and progress polling
The answer chat UI SHALL submit via `POST {API_BASE}/api/v1/answer/agentic/start` and SHALL poll `GET {API_BASE}/api/v1/answer/agentic/{thread_id}/progress` until status leaves `running`, showing live activity steps while waiting. On terminal `completed` or `awaiting_human_review`, the UI SHALL show the same answer, citations, and human-gate behaviors as the agentic chat experience. Resume SHALL remain a direct POST without polling.

#### Scenario: Live steps while running
- **WHEN** the user submits a question
- **AND** progress reports status `running` with activity entries
- **THEN** the UI shows those specialist steps as in-progress or completed activity
- **AND** does not treat the run as failed solely because the final answer is not yet present

#### Scenario: Terminal completed
- **WHEN** progress reports status `completed`
- **THEN** the UI shows the answer and citations when present

#### Scenario: Terminal human review
- **WHEN** progress reports status `awaiting_human_review`
- **THEN** the UI enters the human review state with review reasons
