# Spec Delta: ai-settings-ui

## Purpose

Lets operators inspect and update Metropol runtime chat-model role overrides from the Next.js `/settings` console, including the available-model allowlist and a read-only view of the embedding model.

## ADDED Requirements

### Requirement: Settings page edits runtime chat models
The console SHALL provide a `/settings` route that loads `GET {API}/api/v1/config/models`, lets the operator choose an allowlisted model (or clear to default) for roles `chat`, `composer`, and `prompt_specialist`, saves via `PUT {API}/api/v1/config/models`, and shows success or explicit error states (including 503 when the config store cannot persist).

#### Scenario: Form reflects snapshot
- **WHEN** the operator opens `/settings` and GET succeeds
- **THEN** each chat role shows its effective or selected model
- **AND** the embedding model is shown as non-editable information

#### Scenario: Save success
- **WHEN** the operator saves valid role selections
- **AND** PUT succeeds
- **THEN** the UI shows a success state and refreshed values from the response or a follow-up GET

#### Scenario: Save unavailable
- **WHEN** PUT responds with HTTP 503
- **THEN** the UI shows an unavailable/error state

### Requirement: Settings remains linked from the app shell
The AppShell navigation SHALL continue to include an entry that opens `/settings`.

#### Scenario: Nav entry
- **WHEN** the operator opens the main console shell
- **THEN** a navigation control targets `/settings`
