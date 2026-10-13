# agentic-chat-ui

## ADDED Requirements

### Requirement: Chat shows domain and orchestrator routing
The `/answer` chat UI SHALL display the active run’s Metropol domain (chip or metadata) and SHALL surface orchestrator routing steps from live progress or the terminal payload (next to existing specialist activity), using Astryx components.

#### Scenario: Domain visible on run
- **WHEN** progress or the terminal response includes `domain`
- **THEN** the operator can see that domain on the chat surface without opening raw JSON

#### Scenario: Routing steps visible
- **WHEN** routing history or orchestrator activity entries are present
- **THEN** the UI shows which specialist was chosen (and reason when provided)

### Requirement: Operator can override domain on send
The chat composer SHALL allow choosing domain `auto` or a concrete Metropol domain before send. When not `auto`, the start request SHALL include that `domain`.

#### Scenario: Force Tenela
- **WHEN** the operator selects domain `tenela` and sends a question
- **THEN** the agentic start body includes `domain: tenela`

### Requirement: Agents console for catalog and knobs
The console SHALL provide an `/agents` route (linked from the AppShell SideNav) that loads the server agent catalog and presents agent roles plus configuration knobs relevant to orchestration (at least showing orchestrator max steps and confidence threshold from settings/API). Layout SHALL use Astryx patterns.

#### Scenario: Catalog loads
- **WHEN** the operator opens `/agents`
- **THEN** agents from the catalog endpoint are listed with human-readable labels

#### Scenario: Knobs visible
- **WHEN** `/agents` is open
- **THEN** the operator can see the effective orchestrator step budget and confidence threshold used by the service
