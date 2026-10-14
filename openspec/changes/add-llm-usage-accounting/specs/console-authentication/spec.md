# Spec Delta: console-authentication

## MODIFIED Requirements

### Requirement: Role-based console access
Sessions SHALL carry a role of `usuario` or `administrador`. The console SHALL allow `usuario` to use answer/search (and home) and SHALL restrict settings, ingest, agents studio mutations, user administration, and the usage ledger screen (`/usage`) to `administrador`.

#### Scenario: Usuario blocked from settings
- **WHEN** a signed-in `usuario` opens `/settings`
- **THEN** access is denied (forbidden UI or redirect) and no admin BFF mutation succeeds for that session

#### Scenario: Administrador can open ingest
- **WHEN** a signed-in `administrador` opens `/ingest`
- **THEN** the page is reachable subject to normal API errors

#### Scenario: Administrador reaches usage
- **WHEN** a signed-in `administrador` opens `/usage`
- **THEN** the page is reachable (subject to normal auth)

#### Scenario: Usuario cannot open usage
- **WHEN** a signed-in `usuario` opens `/usage`
- **THEN** access is denied consistently with other administrador-only routes

## ADDED Requirements

### Requirement: Usage upstream is admin-only on the BFF
Same-origin BFF handlers that proxy `GET /api/v1/usage` (and subpaths) SHALL require an authenticated enabled session with role `administrador`, the same class of gate used for config, ingest, and agents admin upstream paths.

#### Scenario: Usuario BFF call to usage is rejected
- **WHEN** a `usuario` session calls the console BFF route that proxies usage summary
- **THEN** the handler rejects the call without forwarding as a successful admin fetch
