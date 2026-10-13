# agentic-answer

## ADDED Requirements

### Requirement: Agentic outcomes expose routing and domain
Agentic completed, paused, and rejected payloads SHALL include the run `domain` and a `routing_history` (or equivalent) listing orchestrator decisions when the orchestrator graph is active. Specialist role names remain Metropol (`intent_framer`, `corpus_fetcher`, `grounded_composer`, `source_guard`, `escalation_gate`).

#### Scenario: Completed run includes domain and routes
- **WHEN** an agentic run completes under the orchestrator topology
- **THEN** the response includes `domain`
- **AND** includes routing history entries for orchestrator dispatches that occurred

### Requirement: Optional domain on agentic submit
Agentic submit endpoints SHALL accept an optional `domain` override. Omitted means auto-detect. Invalid values SHALL yield HTTP 422. Unknown `session_id` behavior remains HTTP 404 before start.

#### Scenario: Submit with domain override
- **WHEN** `POST /answer/agentic/start` includes a valid `domain`
- **THEN** the background run is tagged with that domain
