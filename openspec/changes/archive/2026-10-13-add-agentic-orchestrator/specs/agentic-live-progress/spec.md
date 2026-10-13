# agentic-live-progress

## ADDED Requirements

### Requirement: Progress surfaces orchestrator and domain
While polling progress for a background agentic run, the payload SHALL expose `domain` when known and SHALL include activity or routing information that makes orchestrator decisions visible to operators (node identity and a short reason or summary), without requiring the final answer to be present yet.

#### Scenario: Progress while routing
- **WHEN** the orchestrator has dispatched at least one specialist and status is still `running`
- **THEN** progress activity (or routing fields) reflects that dispatch
- **AND** `domain` is present when already assigned
