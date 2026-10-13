# agentic-chat-ui

## ADDED Requirements

### Requirement: Agents console inspects builtins and manages customs
The `/agents` console SHALL list builtin and custom agents, show builtin details as read-only (including prompt preview when provided by the API), and SHALL provide UI to create, edit, and delete custom agents via the agents API. Layout SHALL use Astryx components.

#### Scenario: Builtin detail is read-only
- **WHEN** the operator selects a builtin agent
- **THEN** the UI shows its metadata and prompt preview when present
- **AND** does not offer edit or delete actions for that builtin

#### Scenario: Create custom from UI
- **WHEN** the operator submits a valid create form for a custom agent
- **THEN** the client calls the create API and refreshes the catalog list on success

#### Scenario: Edit and delete custom from UI
- **WHEN** the operator edits or deletes a custom agent
- **THEN** the client calls the corresponding API and the list reflects the result

### Requirement: Agents console shows orchestrator flow
The `/agents` console SHALL present the effective specialist ladder / flow using catalog data so operators can see how builtins and enabled customs relate.

#### Scenario: Ladder visible
- **WHEN** the catalog response includes ladder information
- **THEN** the UI displays that flow without requiring raw JSON inspection
