# Spec Delta: chat-sessions

## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: List sessions for the console
The system SHALL expose `GET /api/v1/answer/sessions` that returns zero or more session summaries including `session_id`, optional title, timestamps, and turn count, ordered by recent activity, scoped per the ownership rules (console user header or unowned-only when the header is absent).

#### Scenario: Empty list for new console user
- **WHEN** a console user has no owned sessions
- **AND** they list sessions with their `X-Console-User`
- **THEN** the response is HTTP 200 with an empty list even if other users' sessions exist
