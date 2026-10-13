# agentic-chat-ui

## ADDED Requirements

### Requirement: Assistant turn content follows answer-first hierarchy
On `/answer`, an assistant turn (live terminal result or session history) SHALL present content in this order when present: (1) answer text or rejected/review placeholder, (2) custom agent notes, (3) citation evidence. Audit content (routing and agent tool-call flow) SHALL NOT appear above the answer.

#### Scenario: Completed turn with notes and citations
- **WHEN** a completed assistant turn has answer text, non-empty `custom_notes`, and citations
- **THEN** the UI shows the answer before custom notes
- **AND** shows custom notes before citations

#### Scenario: History turn without routing
- **WHEN** a history turn has answer and custom notes but no routing payload
- **THEN** the UI still shows answer then notes (then evidence if any)
- **AND** does not show an empty audit block

### Requirement: Run audit is collapsible
Routing history and agent tool-call / live-flow steps on `/answer` SHALL be presented inside a collapsible audit region. While a run is in progress for the active session, that region SHALL be expanded by default. When the run is terminal for that view, the region SHALL be collapsed by default if it has content. The Metropol domain badge MAY remain visible outside the collapsible when a domain is known.

#### Scenario: Live run expands audit
- **WHEN** the active session is busy with an agentic run and routing or tool-call activity is available
- **THEN** the audit region is expanded so the operator can see progress

#### Scenario: Terminal run collapses audit
- **WHEN** the assistant turn is terminal and audit content exists
- **THEN** the audit region is collapsed by default
- **AND** the operator can expand it to inspect routing or steps
