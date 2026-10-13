# chat-sessions

## Purpose

Provides durable Metropol conversation sessions: multiple parallel chats with a server-side transcript so operators can create, list, open, rename, and delete sessions independently of any single LangGraph `thread_id`.

## Requirements

### Requirement: Create session mints a server id
The system SHALL expose `POST /api/v1/answer/session` that creates a new conversation and returns HTTP 201 with a service-minted `session_id`. Clients MUST NOT supply the new id.

#### Scenario: Create returns id
- **WHEN** a client posts to `/answer/session`
- **THEN** the response is HTTP 201 with a non-empty `session_id`

### Requirement: List sessions for the console
The system SHALL expose `GET /api/v1/answer/sessions` that returns zero or more session summaries including `session_id`, optional title, timestamps, and turn count, ordered by recent activity, scoped per the ownership rules (console user header or unowned-only when the header is absent).

#### Scenario: Empty list
- **WHEN** no sessions exist in the caller's ownership scope
- **THEN** the response is HTTP 200 with an empty list

#### Scenario: Multiple sessions
- **WHEN** several sessions exist in the caller's ownership scope
- **THEN** each summary includes `session_id` and turn_count reflecting closed history turns

#### Scenario: Empty list for new console user
- **WHEN** a console user has no owned sessions
- **AND** they list sessions with their `X-Console-User`
- **THEN** the response is HTTP 200 with an empty list even if other users' sessions exist

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

### Requirement: Rename and delete session
The system SHALL allow `PATCH /api/v1/answer/session/{session_id}` to update the title and `DELETE /api/v1/answer/session/{session_id}` returning HTTP 204 on success.

#### Scenario: Rename
- **WHEN** a client patches a known session with a new title
- **THEN** subsequent reads show that title

#### Scenario: Delete
- **WHEN** a client deletes a known session
- **THEN** later get/list no longer include that session

### Requirement: Session is distinct from graph thread
A `session_id` SHALL identify a conversation that may contain many agentic runs; a `thread_id` SHALL continue to identify a single graph run for progress and resume. Session storage MUST NOT rely on the LangGraph checkpointer tables as the transcript store.

#### Scenario: Parallel concepts
- **WHEN** an operator runs two questions in one session
- **THEN** each run may have its own `thread_id` while sharing the same `session_id`

### Requirement: Session ownership via console user header
When the request includes `X-Console-User` with a non-empty id (at most 64 characters), the system SHALL stamp that value as the session owner on create and SHALL restrict list, read, rename, delete, and agentic use of `session_id` to sessions owned by that id. Sessions with no owner MUST NOT appear in those scoped results. Access to a session that is not owned by the header value SHALL respond like an unknown session (HTTP 404), not a distinct forbidden status.

#### Scenario: Console user lists only own sessions
- **WHEN** two different console user ids each have created sessions (requests carrying their respective `X-Console-User` values)
- **AND** one of them lists sessions with their header
- **THEN** the list includes only that user's sessions

#### Scenario: Foreign session is not found
- **WHEN** a client with `X-Console-User` A requests get, rename, delete, or an agentic operation using a `session_id` owned by user B
- **THEN** the API responds HTTP 404

#### Scenario: Create stamps owner from header
- **WHEN** a client creates a session with a valid `X-Console-User`
- **THEN** subsequent lists with that same header include the new session
- **AND** lists with a different header do not

### Requirement: Unowned sessions without console user header
When `X-Console-User` is absent or empty, the system SHALL create sessions without an owner and SHALL restrict list/read/mutate/agentic session access to unowned sessions only.

#### Scenario: Script mode sees only unowned
- **WHEN** sessions exist both with owners and without
- **AND** a client without `X-Console-User` lists sessions
- **THEN** the response includes only unowned sessions

#### Scenario: Console user does not see unowned
- **WHEN** unowned sessions exist
- **AND** a client with `X-Console-User` lists sessions
- **THEN** those unowned sessions are not included
