# runtime-model-config

## Purpose

Provides runtime overrides for Metropol chat-model roles (defaults from settings, overrides in a shared store) so operators can change which OpenAI chat model each role uses without editing environment files or restarting the API process.

## Requirements

### Requirement: Role-based effective chat models
The system SHALL resolve an effective chat model for each of the roles `chat`, `composer`, and `prompt_specialist`. Resolution SHALL use a role-specific override when set, otherwise the `chat` override when set, otherwise the configured settings default chat model. The embedding model SHALL NOT be overridable through this runtime store.

#### Scenario: Default when no overrides
- **WHEN** no runtime overrides are set for any chat role
- **AND** a completion is requested for role `composer`
- **THEN** the effective model equals the settings default chat model

#### Scenario: Chat override cascades
- **WHEN** only the `chat` role has a runtime override
- **AND** a completion is requested for role `prompt_specialist` with no specialist override
- **THEN** the effective model equals the `chat` override

#### Scenario: Role-specific override wins
- **WHEN** both `chat` and `composer` have runtime overrides
- **AND** a completion is requested for role `composer`
- **THEN** the effective model equals the `composer` override

### Requirement: HTTP get model config snapshot
The backend SHALL expose `GET /api/v1/config/models` returning, for each chat role, effective/default/overridden fields, plus an allowlist of available chat models and the read-only embedding model (or an explicit note that embedding is settings-only). Embedding SHALL NOT appear as a writable override key.

#### Scenario: Get returns snapshot
- **WHEN** a client calls `GET /api/v1/config/models`
- **THEN** the response includes entries for `chat`, `composer`, and `prompt_specialist`
- **AND** includes an available-models allowlist
- **AND** does not treat embedding as a writable override key

### Requirement: HTTP put model config overrides
The backend SHALL expose `PUT /api/v1/config/models` that accepts a map of role keys to model id or null (clear override), validates non-null values against the allowlist (422 if invalid), persists overrides, and returns the updated snapshot. Failed persistence of a write SHALL return 503.

#### Scenario: Put rejects unknown model
- **WHEN** a client PUTs a model id that is not in the allowlist for a role
- **THEN** the response status is 422

#### Scenario: Put clears override with null
- **WHEN** a role has an override
- **AND** a client PUTs `null` for that role
- **THEN** a subsequent GET shows that role as not overridden
- **AND** effective falls back per the resolution rules

### Requirement: Completions use effective models
Answer and agentic chat completions SHALL use the effective model for their role (`chat` for sync answer, `composer` for grounded composition, `prompt_specialist` for custom specialist notes) at request time so a successful PUT is observed on subsequent completions without requiring an API process restart.

#### Scenario: Put affects later completion
- **WHEN** an operator successfully overrides the `composer` role to an allowlisted model
- **AND** a later agentic run reaches grounded composition
- **THEN** that composition call uses the overridden composer model
