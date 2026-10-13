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
The system SHALL expose `POST /api/v1/answer/agentic/{thread_id}/resume` that accepts approve, reject, or adjust and continues or finalizes the paused run.

#### Scenario: Approve after pause
- **WHEN** a paused thread is resumed with approve
- **THEN** the response is HTTP 200 with a completed status and the answer payload for that thread

#### Scenario: Unknown thread
- **WHEN** resume is called with a thread_id that has no paused state
- **THEN** the API responds with HTTP 404

### Requirement: Live progress endpoints are available alongside sync agentic
In addition to the synchronous `POST /api/v1/answer/agentic` path, the system SHALL expose background start and progress polling endpoints as defined by `agentic-live-progress`. The synchronous endpoint behavior SHALL remain unchanged.

#### Scenario: Sync path still completes
- **WHEN** a client posts to `POST /api/v1/answer/agentic` with a valid question and generation is configured
- **THEN** the response remains HTTP 200 or 202 with the existing agentic payload shape
