# agentic-orchestrator

## ADDED Requirements

### Requirement: Enabled custom agents participate in routing
When custom agent profiles are enabled, the agentic orchestrator ladder SHALL be able to dispatch a generic prompt-specialist step for those customs (default placement after corpus fetch and before grounded composition), subject to the existing step budget and legality rules. Disabled customs SHALL NOT be dispatched.

#### Scenario: Enabled custom runs once
- **WHEN** an agentic run executes with an enabled custom profile configured on the ladder
- **THEN** routing history may include a dispatch to that custom specialist
- **AND** the step does not replace corpus fetch or citation ownership of grounded composition

#### Scenario: Disabled custom skipped
- **WHEN** a custom profile exists but is disabled
- **THEN** the orchestrator does not dispatch that custom key
