# agentic-answer

## Purpose

Provides multi-step grounded answers over the Metropol Fintech corpus via an auditable agent pipeline with optional human escalation, parallel to the one-shot answer API.

## Requirements

### Requirement: Agentic answer endpoint accepts a question
The system SHALL expose `POST /api/v1/answer/agentic` that accepts a non-empty question and optional `k`, and returns a payload including run status, agent trace, and when complete an answer with citations.

#### Scenario: Completed run without human pause
- **WHEN** a valid question is submitted and no escalation trigger fires
- **THEN** the response is HTTP 200 with status completed, a non-empty agent_trace, and answer plus citations consistent with retrieved evidence rules used by sync answer

#### Scenario: Missing API key
- **WHEN** the OpenAI API key is not configured and generation would be required
- **THEN** the endpoint responds with HTTP 503 rather than calling the LLM

### Requirement: Agent pipeline runs specialists in fixed order
The system SHALL process each agentic request through the specialist steps intent framing, corpus fetch, grounded composition, and source guard, in that order, before evaluating escalation.

#### Scenario: Trace lists specialists
- **WHEN** an agentic run completes or pauses
- **THEN** agent_trace includes ordered entries covering those specialist steps that executed

### Requirement: Only corpus fetch retrieves evidence
The system SHALL retrieve corpus chunks for an agentic run only in the corpus-fetch step; other specialist steps MUST NOT call the semantic retriever.

#### Scenario: No-evidence path
- **WHEN** corpus fetch returns no hits
- **THEN** the run produces a clear no-evidence outcome without inventing facts, and may escalate per gate rules

### Requirement: Source guard validates citations
The system SHALL mark citations invalid or drop fabricated citation references that do not correspond to evidence retrieved for that run before returning a completed answer.

#### Scenario: Fabricated citation dropped
- **WHEN** composition cites an id or index not present in retrieved hits for the run
- **THEN** that citation is omitted or citations_valid is false according to guard policy, and escalation may trigger

### Requirement: Conditional human escalation
The system SHALL pause the run with HTTP 202 and a thread identifier when escalation reasons are non-empty (including low confidence, no evidence, or invalid citations as configured), and SHALL NOT pause when reasons are empty.

#### Scenario: Pause when reasons present
- **WHEN** the escalation gate computes one or more review reasons
- **THEN** the API responds HTTP 202 with status awaiting human review, thread_id, review_reasons, and agent_trace

#### Scenario: Fall through when no reasons
- **WHEN** the escalation gate computes an empty reason list
- **THEN** the run completes without requiring resume

### Requirement: Resume applies a human decision
The system SHALL expose `POST /api/v1/answer/agentic/{thread_id}/resume` that accepts approve, reject, or adjust and continues or finalizes the paused run. With the durable checkpointer configured, “paused state” SHALL be the checkpointed LangGraph state for that `thread_id` in the shared database, not merely in-process memory.

#### Scenario: Approve after pause
- **WHEN** a paused thread is resumed with approve
- **THEN** the response is HTTP 200 with a completed status and the answer payload for that thread

#### Scenario: Unknown thread
- **WHEN** resume is called with a thread_id that has no paused checkpoint state
- **THEN** the API responds with HTTP 404

### Requirement: Live progress endpoints are available alongside sync agentic
In addition to the synchronous `POST /api/v1/answer/agentic` path, the system SHALL expose background start and progress polling endpoints as defined by `agentic-live-progress`. The synchronous endpoint behavior SHALL remain unchanged.

#### Scenario: Sync path still completes
- **WHEN** a client posts to `POST /api/v1/answer/agentic` with a valid question and generation is configured
- **THEN** the response remains HTTP 200 or 202 with the existing agentic payload shape

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
