# Spec Delta

## Purpose

Lets operators ask Metropol Fintech questions from the Next.js console and see a grounded answer with citations from the existing sync answer API.

## ADDED Requirements

### Requirement: Chat route is reachable from the shell
The frontend SHALL expose a dedicated answer chat route (path `/answer`) linked from the main application side navigation inside the existing app shell.

#### Scenario: Navigate to chat
- **WHEN** a user opens the application shell
- **AND** selects the answer chat navigation item
- **THEN** the chat route is shown without leaving the shell layout

### Requirement: User can submit a question to sync answer
The chat UI SHALL accept a non-empty question and optional retrieval depth `k`, and SHALL call `POST {API_BASE}/api/v1/answer` with that payload.

#### Scenario: Successful submit
- **WHEN** the user enters a question and submits
- **AND** the API returns HTTP 200 with an answer payload
- **THEN** the UI shows the answer text
- **AND** shows citations when the payload includes them

#### Scenario: Optional k
- **WHEN** the user provides a valid `k`
- **AND** submits
- **THEN** the request body includes that `k`

### Requirement: Loading and error states are visible
While a request is in flight the UI SHALL show a loading state and SHALL prevent duplicate submits. On failure the UI SHALL show an error state that distinguishes missing-key style service unavailability (HTTP 503) from other network or HTTP errors when the status is known.

#### Scenario: Loading
- **WHEN** the user has submitted and the response has not arrived
- **THEN** a loading indicator is visible
- **AND** submit is disabled

#### Scenario: API key missing (503)
- **WHEN** the answer API responds with HTTP 503
- **THEN** the UI shows an error explaining the service is unavailable
- **AND** does not show a fabricated answer

#### Scenario: Network or other HTTP error
- **WHEN** the request fails for a reason other than a successful 200 payload
- **THEN** the UI shows an error state
- **AND** does not treat the turn as success

### Requirement: Citations display source provenance
When the answer payload includes citations, the UI SHALL list each citation with at least its source path and excerpt.

#### Scenario: Citations listed
- **WHEN** a successful response includes one or more citations
- **THEN** each citation shows `source_path` and `excerpt`

#### Scenario: No evidence
- **WHEN** a successful response indicates no evidence (`no_evidence` true or empty citations with a no-evidence answer)
- **THEN** the UI still shows the answer text
- **AND** does not invent citation rows

### Requirement: API base URL is configurable
The frontend SHALL read the answer API origin from `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000` when unset, and SHALL document that variable for local development.

#### Scenario: Default base URL
- **WHEN** `NEXT_PUBLIC_API_BASE_URL` is unset
- **THEN** requests target `http://localhost:8000`

#### Scenario: Custom base URL
- **WHEN** `NEXT_PUBLIC_API_BASE_URL` is set to a valid origin
- **THEN** requests target that origin
