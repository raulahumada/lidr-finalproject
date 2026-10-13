# agentic-answer

## ADDED Requirements

### Requirement: Paused agentic state survives API process restart
When the durable Postgres checkpointer is configured (default whenever `DATABASE_URL` is set for production-shaped runs), the system SHALL persist LangGraph pause state for agentic threads so that a `thread_id` left in `awaiting_human_review` remains resumable via `POST /api/v1/answer/agentic/{thread_id}/resume` after the API process restarts. Test or explicitly configured memory-only mode MAY use an in-process saver and MUST document that pause state does not survive restart in that mode.

#### Scenario: Resume after process restart
- **WHEN** an agentic run pauses for human review with a `thread_id`
- **AND** the API process restarts while the durable checkpointer remains configured against the same database
- **AND** a client calls resume on that `thread_id` with a valid decision
- **THEN** the API continues or finalizes the paused run (HTTP 200 with a completed outcome, or the documented reject/adjust behavior) rather than treating the thread as unknown solely because of the restart

#### Scenario: Memory-only mode for tests
- **WHEN** the agentic checkpointer is configured for in-process memory (tests or explicit offline flag)
- **THEN** pause/resume still works within the same process lifetime
- **AND** operators or developers are not promised durability across restarts in that mode

## MODIFIED Requirements

### Requirement: Resume applies a human decision
The system SHALL expose `POST /api/v1/answer/agentic/{thread_id}/resume` that accepts approve, reject, or adjust and continues or finalizes the paused run. With the durable checkpointer configured, “paused state” SHALL be the checkpointed LangGraph state for that `thread_id` in the shared database, not merely in-process memory.

#### Scenario: Approve after pause
- **WHEN** a paused thread is resumed with approve
- **THEN** the response is HTTP 200 with a completed status and the answer payload for that thread

#### Scenario: Unknown thread
- **WHEN** resume is called with a thread_id that has no paused checkpoint state
- **THEN** the API responds with HTTP 404
