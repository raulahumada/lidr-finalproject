# conversation-memory

## ADDED Requirements

### Requirement: Session accumulates conversation facts
When an agentic run is bound to a `session_id`, the system SHALL derive and merge structured conversation facts from the turn (at least domain when known and cited document identifiers when citations exist) without a dedicated LLM extraction call. Facts SHALL be available to subsequent turns in that session for resolution and memory rendering. Without `session_id`, fact accumulation SHALL be a no-op.

#### Scenario: Facts merge after cited turn
- **WHEN** a completed agentic turn with `session_id` includes citations
- **THEN** the session’s stored facts include those cited document identifiers for later turns

### Requirement: Explicit scoping phrases become anchors
The system SHALL detect conservative Spanish scoping phrases in the user question that pin conversation scope (for example “de acá en adelante” / “solo cobranzas”) and store them as anchors for the session. Anchors SHALL bias later resolve/retrieve when no stronger per-request domain override is supplied. Ambiguous mentions that are not scoping pins MUST NOT create anchors.

#### Scenario: Scoping pin stored
- **WHEN** the user says a clear scoping pin such as limiting further questions to cobranzas
- **THEN** a session anchor is recorded reflecting that scope

#### Scenario: Mere mention is not an anchor
- **WHEN** the user mentions a domain without a scoping pin
- **THEN** no new anchor is created from that mention alone

#### Scenario: Scope-pin-only turn does not RAG-compose
- **WHEN** the user message is only an explicit scoping pin (no content question)
- **THEN** the system confirms the pinned domain, records the anchor, and does not retrieve or compose a corpus answer for that turn

### Requirement: Facts and anchors appear in budgeted memory
`render_memory` (or equivalent) SHALL include active facts and anchors in the memory block subject to the existing evidence-wins token budget.

#### Scenario: Memory block lists anchors
- **WHEN** a session has at least one anchor and memory is rendered for composition
- **THEN** the memory block text includes that anchor scope
