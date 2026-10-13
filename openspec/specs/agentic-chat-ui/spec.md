# agentic-chat-ui Specification

## Purpose
Lets operators run Metropol Fintech agentic Q&A from the Next.js console: submit a question, inspect the agent trace, handle human escalation, and resume with approve, reject, or adjust against the existing agentic answer API.

## Requirements

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

### Requirement: Operator can manage multiple chat sessions
The answer chat UI SHALL let the operator create a new session, list existing sessions, switch the active session, and delete or rename when those actions are exposed, using the `chat-sessions` API. Layout SHALL use Astryx components consistent with the `ai-chat` template patterns (no ad-hoc page structure with raw layout primitives).

#### Scenario: New chat
- **WHEN** the operator starts a new chat
- **THEN** the UI creates a session via the API and makes it active

#### Scenario: Switch session
- **WHEN** the operator selects another session from the list
- **THEN** the message thread shows that session’s history from the server

### Requirement: Session deep link restores transcript
The UI SHALL support opening `/answer?session=<session_id>` by loading that session’s history into the chat thread. If the id is unknown, the UI SHALL show a clear error or empty-state recovery without crashing.

#### Scenario: Reload with query param
- **WHEN** the page loads with a valid `session` query param
- **THEN** prior history turns for that session are visible without re-asking

### Requirement: Sends include active session_id
While a session is active, agentic start (live progress hot path) SHALL include that `session_id` so completed turns persist to the server transcript.

#### Scenario: Submit in session
- **WHEN** the operator sends a question with an active session
- **THEN** the start request body includes that `session_id`

### Requirement: Chat shows domain and orchestrator routing
The `/answer` chat UI SHALL display the active run’s Metropol domain (chip or metadata) and SHALL surface orchestrator routing steps from live progress or the terminal payload (next to existing specialist activity), using Astryx components.

#### Scenario: Domain visible on run
- **WHEN** progress or the terminal response includes `domain`
- **THEN** the operator can see that domain on the chat surface without opening raw JSON

#### Scenario: Routing steps visible
- **WHEN** routing history or orchestrator activity entries are present
- **THEN** the UI shows which specialist was chosen (and reason when provided)

### Requirement: Operator can override domain on send
The chat composer SHALL allow choosing domain `auto` or a concrete Metropol domain before send. When not `auto`, the start request SHALL include that `domain`.

#### Scenario: Force Tenela
- **WHEN** the operator selects domain `tenela` and sends a question
- **THEN** the agentic start body includes `domain: tenela`

### Requirement: Agents console for catalog and knobs
The console SHALL provide an `/agents` route (linked from the AppShell SideNav) that loads the server agent catalog and presents agent roles plus configuration knobs relevant to orchestration (at least showing orchestrator max steps and confidence threshold from settings/API). Layout SHALL use Astryx patterns.

#### Scenario: Catalog loads
- **WHEN** the operator opens `/agents`
- **THEN** agents from the catalog endpoint are listed with human-readable labels

#### Scenario: Knobs visible
- **WHEN** `/agents` is open
- **THEN** the operator can see the effective orchestrator step budget and confidence threshold used by the service
