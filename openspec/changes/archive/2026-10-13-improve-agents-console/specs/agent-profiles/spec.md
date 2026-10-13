# agent-profiles

## Purpose

Lets operators create, update, and delete custom LLM agent profiles stored in the database, while pipeline builtin agents remain code-defined and immutable through the API.

## ADDED Requirements

### Requirement: Custom agent profiles are persisted
The system SHALL store custom agent profiles in durable storage (Postgres) with at least: unique `key`, `label`, `role`, `system_prompt`, and `enabled`. Built-in pipeline agent definitions MUST NOT be stored as mutable rows for the purpose of editing builtins.

#### Scenario: Create custom profile
- **WHEN** a client creates a custom agent with a new key and non-empty system prompt
- **THEN** the profile is persisted and appears in subsequent catalog listings as custom

#### Scenario: Reserved builtin key rejected
- **WHEN** a client tries to create a custom agent whose key matches a builtin pipeline agent
- **THEN** the API rejects the request with a conflict or validation error and does not persist a row

### Requirement: Custom profiles support update and delete
The system SHALL allow updating and deleting custom profiles by key. Attempts to update or delete a builtin key SHALL fail without modifying builtin behavior.

#### Scenario: Patch custom
- **WHEN** a client patches an existing custom agent
- **THEN** persisted fields are updated and later GETs reflect the change

#### Scenario: Delete custom
- **WHEN** a client deletes an existing custom agent
- **THEN** the profile is removed and no longer appears in the catalog

#### Scenario: Mutate builtin rejected
- **WHEN** a client PATCHes or DELETEs a builtin agent key
- **THEN** the API responds with an error indicating the agent is not mutable
- **AND** builtin catalog behavior is unchanged

### Requirement: Catalog merges builtins and customs
`GET` catalog endpoints SHALL return builtin agents (read-only metadata, including prompt preview for LLM builtins when available) together with custom agents from storage, plus ladder and knobs information needed by the console.

#### Scenario: List includes both kinds
- **WHEN** at least one custom profile exists
- **THEN** the catalog response includes both builtin and custom entries distinguishable by kind or equivalent flag

#### Scenario: Builtin prompt preview
- **WHEN** the catalog includes an LLM-driven builtin that uses versioned answer prompts
- **THEN** the response includes a read-only prompt preview derived from the active Jinja templates (not a DB override)
