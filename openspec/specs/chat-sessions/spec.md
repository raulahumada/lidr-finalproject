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
The system SHALL expose `GET /api/v1/answer/sessions` that returns zero or more session summaries including `session_id`, optional title, timestamps, and turn count, ordered by recent activity.

#### Scenario: Empty list
- **WHEN** no sessions exist
- **THEN** the response is HTTP 200 with an empty list

#### Scenario: Multiple sessions
- **WHEN** several sessions exist
- **THEN** each summary includes `session_id` and turn_count reflecting closed history turns

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
