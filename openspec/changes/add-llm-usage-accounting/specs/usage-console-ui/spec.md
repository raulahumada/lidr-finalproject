# Spec Delta: usage-console-ui

## Purpose

Gives Metropol console administrators a dedicated screen to inspect durable LLM token usage aggregates from the backend summary API, without exposing service credentials to the browser.

## ADDED Requirements

### Requirement: Admin usage page shows summary aggregates
The console SHALL provide an admin-only `/usage` page that loads `GET` usage summary data via a same-origin BFF and displays total calls, total input/output/total tokens, and a per-model breakdown. The page SHALL NOT display estimated USD costs.

#### Scenario: Admin sees totals and by-model table
- **WHEN** an administrador opens `/usage` and the summary returns non-empty aggregates
- **THEN** the page shows total calls and token sums
- **AND** shows a table (or equivalent) of per-model calls and token counts
- **AND** does not show a USD cost column

### Requirement: Usage filters forward to the summary API
The usage page SHALL allow filtering by date range, optional `purpose`, and optional `session_id`, and SHALL refetch the summary with those query parameters. An inverted or invalid range that the API rejects SHALL surface an error without silently clearing the last successful totals.

#### Scenario: Apply filters refetches summary
- **WHEN** an administrador sets a valid from/to range and optional purpose or session id and applies filters
- **THEN** the BFF is called with the corresponding query parameters
- **AND** the displayed aggregates update from the new response

#### Scenario: API 422 keeps prior totals
- **WHEN** the summary API responds 422 for the requested filters
- **THEN** the page shows an error
- **AND** keeps displaying the last successful totals

### Requirement: Non-admin cannot open usage
Unauthenticated visitors and sessions with role `usuario` SHALL NOT access `/usage` (redirect or deny consistent with other admin screens).

#### Scenario: Usuario is blocked from usage
- **WHEN** a signed-in `usuario` navigates to `/usage`
- **THEN** access is denied the same way as other administrador-only console routes
