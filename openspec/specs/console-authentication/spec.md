# console-authentication

## Purpose

Authenticates Metropol console operators with Auth.js (session + roles), stores identity separately from the RAG database, and relays browser API calls through a same-origin BFF that attaches the FastAPI service token so the secret never reaches client JavaScript.

## Requirements

### Requirement: Console login and registration
The Next.js console SHALL provide login with email/password credentials (Google OAuth when configured in a future enablement) and self-service registration. Newly registered accounts SHALL be created disabled and MUST NOT access console routes until an administrator enables them. Unauthenticated visitors SHALL be redirected to login for console pages (auth routes themselves remain reachable).

#### Scenario: Unauthenticated redirect
- **WHEN** an unauthenticated user opens a console page such as `/answer`
- **THEN** they are redirected to the login flow

#### Scenario: Disabled account blocked
- **WHEN** a user registers successfully
- **AND** an administrator has not enabled the account
- **THEN** the user cannot use console features that require an enabled session

### Requirement: Role-based console access
Sessions SHALL carry a role of `usuario` or `administrador`. The console SHALL allow `usuario` to use answer/search (and home) and SHALL restrict settings, ingest, agents studio mutations, and user administration to `administrador`.

#### Scenario: Usuario blocked from settings
- **WHEN** a signed-in `usuario` opens `/settings`
- **THEN** access is denied (forbidden UI or redirect) and no admin BFF mutation succeeds for that session

#### Scenario: Administrador can open ingest
- **WHEN** a signed-in `administrador` opens `/ingest`
- **THEN** the page is reachable subject to normal API errors

### Requirement: Identity database isolation
Console identity data SHALL persist in a database configured by `AUTH_DATABASE_URL` (or equivalent) that is not the RAG/corpus schema used by Alembic document/chunk tables.

#### Scenario: Separate identity store
- **WHEN** operators inspect configuration
- **THEN** auth identity is configured via a dedicated auth database URL distinct from the corpus `DATABASE_URL`

### Requirement: Same-origin BFF attaches service token
Browser code SHALL call same-origin Next Route Handlers for Metropol API operations used by the console. Those handlers SHALL attach the configured service bearer token when calling FastAPI and SHALL NOT expose `SERVICE_TOKEN` via `NEXT_PUBLIC_` environment variables. Handlers SHALL require an authenticated enabled session (except Auth.js routes); admin-only upstream operations SHALL require `administrador`.

#### Scenario: Browser does not hold service token
- **WHEN** the production frontend bundle is inspected for configuration
- **THEN** it does not embed the service token as a public env value

#### Scenario: BFF rejects anonymous relay
- **WHEN** an unauthenticated client calls a BFF relay route that fronts a protected FastAPI operation
- **THEN** the BFF responds with an authentication error and does not successfully call FastAPI as an anonymous browser

#### Scenario: Console clients use BFF
- **WHEN** the answer or search UI performs an API request
- **THEN** the request targets the same origin BFF path space rather than a public browser-held FastAPI base URL for that operation
