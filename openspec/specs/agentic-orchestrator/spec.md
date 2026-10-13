# agentic-orchestrator

## Purpose

Turns the Metropol agentic answer graph into a star multi-agent system: an orchestrator hub routes pipeline specialists under a step budget, exposes a server-side agent catalog, and tags each run with a Metropol business domain for light bias and operator visibility.

## Requirements

### Requirement: Agentic graph is a star with an orchestrator hub
The agentic answer graph SHALL route through an `orchestrator` node that selects the next pipeline specialist via dynamic hand-off (`Command(goto)` or equivalent). Specialists SHALL return to the orchestrator (or proceed to the human escalation gate when the run is ready to finish). The fixed linear-only edge chain without a hub SHALL no longer be the sole topology.

#### Scenario: Hub dispatches specialists
- **WHEN** an agentic run starts
- **THEN** control passes through the orchestrator before each specialist step that the ladder still requires
- **AND** a routing history entry records the chosen next agent and a reason

#### Scenario: Step budget stops the hub
- **WHEN** orchestrator steps reach the configured maximum
- **THEN** the hub finishes routing toward the escalation gate (or terminal finish path)
- **AND** the reason indicates the step budget was exhausted

### Requirement: Routing uses a deterministic legal ladder
Orchestrator selection SHALL be deterministic: a fixed specialist order with legality checks (preconditions met; illegal re-runs avoided). The system SHALL NOT require an LLM supervisor to choose the next agent in v1.

#### Scenario: Ladder follows pipeline order
- **WHEN** no specialist has run yet and a question is present
- **THEN** the first legal specialist on the Metropol ladder is selected (intent framing before corpus fetch, and so on)

#### Scenario: Illegal target overridden
- **WHEN** a proposed next agent is not legal given state
- **THEN** the hub overrides to the next legal ladder agent or finish
- **AND** the routing history records the override reason

### Requirement: Server agent catalog is the source of truth
The system SHALL expose `GET /api/v1/answer/agents` (or equivalent under the answer API prefix) returning the catalog of orchestrator and specialist agents (key, label, role summary, whether LLM-driven, allowed tools if any). Clients MUST NOT invent a divergent hard-coded agent list as the authoritative catalog.

#### Scenario: Catalog lists Metropol specialists
- **WHEN** a client calls the agents catalog endpoint
- **THEN** the response includes the orchestrator and the pipeline specialists used by the agentic graph
- **AND** labels are suitable for operator UI

### Requirement: Runs carry a Metropol domain tag
Each agentic run SHALL carry a `domain` value in `{ventas, cobranzas, operacion, tenela, general}`. When the client omits an override, the system SHALL assign a domain automatically from the question (and session context when available). When the client supplies a valid override, that value SHALL win. Domain MAY lightly bias framing or composition; it MUST NOT invent citations.

#### Scenario: Auto domain
- **WHEN** agentic start has no domain override and the question clearly concerns cobranzas
- **THEN** `domain` is `cobranzas` on the run outcome / progress payload

#### Scenario: Override domain
- **WHEN** the client sends domain `tenela`
- **THEN** the run uses `tenela` regardless of auto-detect

#### Scenario: Unknown override rejected
- **WHEN** the client sends an unsupported domain string
- **THEN** the API responds with HTTP 422 before starting the graph

### Requirement: Enabled custom agents participate in routing
When custom agent profiles are enabled, the agentic orchestrator ladder SHALL be able to dispatch a generic prompt-specialist step for those customs (default placement after corpus fetch and before grounded composition), subject to the existing step budget and legality rules. Disabled customs SHALL NOT be dispatched.

#### Scenario: Enabled custom runs once
- **WHEN** an agentic run executes with an enabled custom profile configured on the ladder
- **THEN** routing history may include a dispatch to that custom specialist
- **AND** the step does not replace corpus fetch or citation ownership of grounded composition

#### Scenario: Disabled custom skipped
- **WHEN** a custom profile exists but is disabled
- **THEN** the orchestrator does not dispatch that custom key
