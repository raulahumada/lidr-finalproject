# search-console-ui

## Purpose

Lets operators run Metropol semantic search from the Next.js console: submit a query, inspect ranked chunk hits (score, source path, excerpt), and debug retrieval without invoking answer generation.

## ADDED Requirements

### Requirement: Operator can search the corpus from the console
The console SHALL provide a `/search` route where the operator submits a non-empty query (and optional `k`) to `POST {API}/api/v1/search` and sees results or an explicit empty/error state.

#### Scenario: Hits listed
- **WHEN** search returns one or more results
- **THEN** each hit shows at least score, source path, and excerpt

#### Scenario: Empty results
- **WHEN** search returns an empty results list
- **THEN** the UI shows an empty state (not a fabricated hit)

#### Scenario: Service unavailable
- **WHEN** search responds with HTTP 503
- **THEN** the UI shows an unavailable-service error

### Requirement: Search is linked from the app shell
The AppShell navigation SHALL include an entry that opens the search console route.

#### Scenario: Nav entry
- **WHEN** the operator opens the main console shell
- **THEN** a navigation control targets `/search`
