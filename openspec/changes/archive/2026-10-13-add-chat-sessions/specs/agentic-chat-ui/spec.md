# agentic-chat-ui

## ADDED Requirements

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
