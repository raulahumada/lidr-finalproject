# answer-chat-ui

## MODIFIED Requirements

### Requirement: Chat route is reachable from the shell
The frontend SHALL expose a dedicated answer chat route (path `/answer`) linked from the main application side navigation inside the existing app shell. That route SHALL host the primary agentic chat experience defined by `agentic-chat-ui`.

#### Scenario: Navigate to chat
- **WHEN** a user opens the application shell
- **AND** selects the answer chat navigation item
- **THEN** the chat route is shown without leaving the shell layout

### Requirement: User can submit a question to sync answer
The chat UI MAY offer an optional secondary path that calls `POST {API_BASE}/api/v1/answer` for one-shot sync answers. When that secondary path is present, it SHALL accept a non-empty question and optional `k` and SHALL show answer text and citations on HTTP 200. The primary submit path on `/answer` SHALL be agentic as specified by `agentic-chat-ui`.

#### Scenario: Successful submit
- **WHEN** the UI exposes a sync submit control
- **AND** the user enters a question and submits through that control
- **AND** the sync API returns HTTP 200 with an answer payload
- **THEN** the UI shows the answer text
- **AND** shows citations when the payload includes them

#### Scenario: Optional k
- **WHEN** the UI exposes a sync submit control
- **AND** the user provides a valid `k`
- **AND** submits through that sync control
- **THEN** the request body includes that `k`

#### Scenario: Primary path remains agentic
- **WHEN** the user uses the default submit control on `/answer`
- **THEN** the client calls the agentic answer endpoint rather than only the sync endpoint

### Requirement: Loading and error states are visible
While a request is in flight the UI SHALL show a loading state and SHALL prevent duplicate submits. On failure the UI SHALL show an error state that distinguishes missing-key style service unavailability (HTTP 503) from other network or HTTP errors when the status is known. Agentic-specific loading, 202 pause, and resume errors are owned by `agentic-chat-ui`.

#### Scenario: Loading
- **WHEN** the user has submitted and the response has not arrived
- **THEN** a loading indicator is visible
- **AND** submit is disabled

#### Scenario: API key missing (503)
- **WHEN** the answer API responds with HTTP 503
- **THEN** the UI shows an error explaining the service is unavailable
- **AND** does not show a fabricated answer

#### Scenario: Network or other HTTP error
- **WHEN** the request fails for a reason other than a successful payload (including successful agentic 202 pause handled elsewhere)
- **THEN** the UI shows an error state
- **AND** does not treat the turn as success

### Requirement: Citations display source provenance
When an answer payload includes citations, the UI SHALL list each citation with at least its source path and excerpt.

#### Scenario: Citations listed
- **WHEN** a successful response includes one or more citations
- **THEN** each citation shows `source_path` and `excerpt`

#### Scenario: No evidence
- **WHEN** a successful response indicates no evidence (`no_evidence` true or empty citations with a no-evidence answer)
- **THEN** the UI still shows the answer text
- **AND** does not invent citation rows

### Requirement: API base URL is configurable
The frontend SHALL read the answer API origin from `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000` when unset, and SHALL document that variable for local development. The same base URL SHALL be used for sync and agentic clients.

#### Scenario: Default base URL
- **WHEN** `NEXT_PUBLIC_API_BASE_URL` is unset
- **THEN** requests target `http://localhost:8000`

#### Scenario: Custom base URL
- **WHEN** `NEXT_PUBLIC_API_BASE_URL` is set to a valid origin
- **THEN** requests target that origin
