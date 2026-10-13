# agentic-live-progress

## MODIFIED Requirements

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
