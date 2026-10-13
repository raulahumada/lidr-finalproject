# Spec Delta: service-authentication

## Purpose

Protects the Metropol FastAPI service with a shared bearer service token so only trusted server-side callers (the Next BFF and local scripts that know the secret) can invoke API routes when a token is configured.

## ADDED Requirements

### Requirement: Bearer service token gate
When `SERVICE_TOKEN` is configured (non-empty), the API SHALL require `Authorization: Bearer <token>` matching that value using a constant-time comparison for all routes under the API prefix except explicitly exempt health access. Requests without a valid token SHALL receive HTTP 401 and MUST NOT execute the route handler.

#### Scenario: Missing token when configured
- **WHEN** `SERVICE_TOKEN` is set
- **AND** a client calls a protected route without `Authorization`
- **THEN** the response status is 401

#### Scenario: Valid token
- **WHEN** `SERVICE_TOKEN` is set
- **AND** a client calls a protected route with the correct bearer token
- **THEN** the route executes normally

### Requirement: Health remains open
`GET {api_prefix}/health` SHALL succeed without a bearer token even when `SERVICE_TOKEN` is configured.

#### Scenario: Health without credentials
- **WHEN** `SERVICE_TOKEN` is set
- **AND** a client calls the health endpoint without Authorization
- **THEN** the response status is 200

### Requirement: Open mode when token unset in non-production
When `SERVICE_TOKEN` is empty and the app environment is not production, the API SHALL accept requests without a bearer token and SHALL emit a clear boot-time warning that the service is open.

#### Scenario: Local open mode
- **WHEN** the service starts with empty `SERVICE_TOKEN` and non-production environment
- **THEN** protected routes remain callable without Authorization
- **AND** a warning is logged at startup

### Requirement: Production refuses empty token
When the app environment is production and `SERVICE_TOKEN` is empty, the process SHALL refuse to start successfully (fail closed).

#### Scenario: Production misconfiguration
- **WHEN** production environment is selected
- **AND** `SERVICE_TOKEN` is empty
- **THEN** the application does not serve traffic as a healthy process
