# ingest-console-ui

## Purpose

Lets operators inspect Metropol corpus index stats and start or force a corpus ingest run from the Next.js console, then poll until a summary appears, without using the terminal CLI.

## Requirements

### Requirement: Operator can view corpus stats and start ingest from the console
The console SHALL provide an `/ingest` route that loads corpus stats from `GET {API}/api/v1/ingest/stats`, lets the operator optionally enable force re-ingest, starts a run via `POST {API}/api/v1/ingest/runs`, and polls `GET {API}/api/v1/ingest/runs/{run_id}` until the run reaches a terminal status, showing summary counts or an explicit error/unavailable state.

#### Scenario: Stats rendered
- **WHEN** the operator opens `/ingest` and stats succeed
- **THEN** the UI shows document count, chunk count, and the configured corpus root (or a clear missing-config state)

#### Scenario: Run completes with summary
- **WHEN** the operator starts an ingest run
- **AND** the run reaches `completed`
- **THEN** the UI shows summary counts from the poll response

#### Scenario: Service unavailable on start
- **WHEN** start responds with HTTP 503
- **THEN** the UI shows an unavailable/misconfigured-service error

#### Scenario: Busy rejected
- **WHEN** start responds with HTTP 409
- **THEN** the UI shows that another ingest run is already in progress

### Requirement: Ingest is linked from the app shell and home
The AppShell navigation SHALL include an entry that opens `/ingest`. The home console SHALL include a CTA that navigates to `/ingest`.

#### Scenario: Nav entry
- **WHEN** the operator opens the main console shell
- **THEN** a navigation control targets `/ingest`

#### Scenario: Home CTA
- **WHEN** the operator opens the home route `/`
- **THEN** a control navigates to `/ingest`

### Requirement: Completed ingest offers a path to search
After a successful ingest summary is shown, the UI SHALL offer a control that navigates to the search console (`/search`).

#### Scenario: CTA to search
- **WHEN** a run completes successfully and the summary is visible
- **THEN** a control targets `/search`
