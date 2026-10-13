# Spec Delta

## Purpose

Lets operators run Metropol Fintech agentic Q&A from the Next.js console: submit a question, inspect the agent trace, handle human escalation, and resume with approve, reject, or adjust against the existing agentic answer API.

## ADDED Requirements

### Requirement: User can submit a question to agentic answer
The chat UI SHALL accept a non-empty question and optional retrieval depth `k`, and SHALL call `POST {API_BASE}/api/v1/answer/agentic` with that payload as the primary submit path on the answer chat route.

#### Scenario: Completed without pause
- **WHEN** the user enters a question and submits
- **AND** the API returns HTTP 200 with status `completed`
- **THEN** the UI shows the answer text when present
- **AND** shows citations when the payload includes them
- **AND** shows the agent trace steps when present

#### Scenario: Optional k
- **WHEN** the user provides a valid `k`
- **AND** submits to agentic answer
- **THEN** the request body includes that `k`

### Requirement: HTTP 202 pause is a review state not an error
When the agentic API responds with HTTP 202 and status `awaiting_human_review`, the UI SHALL treat the response as a successful pause requiring human review, and SHALL NOT present it as a failed request.

#### Scenario: Awaiting human review
- **WHEN** the agentic submit returns HTTP 202 with status `awaiting_human_review`
- **THEN** the UI enters a review state
- **AND** shows `review_reasons` when provided
- **AND** does not show a generic failure banner for that 202 response

### Requirement: Human gate supports approve reject and adjust
While in `awaiting_human_review`, the UI SHALL offer actions to resume with `approve`, `reject`, or `adjust`, calling `POST {API_BASE}/api/v1/answer/agentic/{thread_id}/resume` with the chosen decision. For `adjust`, the UI SHALL allow the operator to supply an adjusted answer text before resume.

#### Scenario: Approve
- **WHEN** a paused run is shown
- **AND** the operator chooses approve
- **THEN** the client posts resume with decision `approve`
- **AND** on HTTP 200 the UI reflects the completed (or otherwise returned) status and answer payload

#### Scenario: Adjust with edited answer
- **WHEN** a paused run is shown
- **AND** the operator chooses adjust and provides adjusted answer text
- **THEN** the client posts resume with decision `adjust` and that adjusted answer

#### Scenario: Reject
- **WHEN** a paused run is shown
- **AND** the operator chooses reject
- **THEN** the client posts resume with decision `reject`
- **AND** the UI reflects a rejected outcome without inventing a completed answer

### Requirement: Agent trace is visible
When an agentic response includes `agent_trace`, the UI SHALL present the ordered specialist steps (at least each step’s node identity and summary) so operators can audit the run.

#### Scenario: Trace listed
- **WHEN** a completed or paused response includes one or more trace steps
- **THEN** each step’s node and summary are visible in the chat transcript or an adjacent audit surface

### Requirement: Citations display source provenance for agentic answers
When an agentic response includes citations, the UI SHALL list each citation with at least its source path and excerpt.

#### Scenario: Citations listed
- **WHEN** a successful agentic response includes one or more citations
- **THEN** each citation shows `source_path` and `excerpt`

### Requirement: Agentic loading and error states are visible
While an agentic submit or resume request is in flight the UI SHALL show a loading state and SHALL prevent duplicate submit or resume actions. On failure the UI SHALL show an error state that distinguishes service unavailability (HTTP 503), unknown or expired thread (HTTP 404 on resume), and other network or HTTP errors when the status is known.

#### Scenario: Loading blocks duplicate actions
- **WHEN** submit or resume is in flight
- **THEN** a loading indicator is visible
- **AND** duplicate submit and resume actions are disabled

#### Scenario: Missing API key (503)
- **WHEN** the agentic API responds with HTTP 503
- **THEN** the UI shows an unavailable-service error
- **AND** does not show a fabricated answer

#### Scenario: Unknown thread (404)
- **WHEN** resume is called and the API responds with HTTP 404
- **THEN** the UI shows an error explaining the thread is unknown or no longer paused
- **AND** does not invent a completed answer

### Requirement: Thread identifier is available for paused runs
When the UI is in `awaiting_human_review`, it SHALL expose the `thread_id` in operator-visible metadata (not as the primary headline) so a paused run can be correlated with backend logs.

#### Scenario: Thread id shown on pause
- **WHEN** status is `awaiting_human_review`
- **THEN** the `thread_id` is visible in supporting metadata on the page
