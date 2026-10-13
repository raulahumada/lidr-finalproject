# conversation-memory

## Purpose

Gives Metropol agentic turns usable conversation memory: resolve referential follow-ups before retrieval, attach a budgeted recent-turn block to synthesis (not citable evidence), and persist session facts/anchors for durable scope without a second LLM extract.

## Requirements

### Requirement: Referential questions resolve before retrieval
When an agentic run is bound to a session with prior closed turns, the system SHALL produce a `resolved_question` suitable for retrieval before corpus fetch. Resolution SHALL be conservative and deterministic: if the written question already names its subject, or no clear referent exists in prior turns, `resolved_question` SHALL equal the written question. The system SHALL NOT invent referents.

#### Scenario: Follow-up is rewritten
- **WHEN** the prior turn established a concrete subject (e.g. a product or process named in the last question/answer)
- **AND** the new question is referential (e.g. starts with “¿y …” / uses a standalone demonstrative pronoun)
- **THEN** `resolved_question` includes an explicit referent derived from that prior turn
- **AND** corpus retrieval uses `resolved_question` (via the framed query)

#### Scenario: Self-contained question is unchanged
- **WHEN** the new question already names its subject
- **THEN** `resolved_question` equals the written question
- **AND** no referent substitution is recorded

#### Scenario: No prior turns
- **WHEN** the session has an empty history window
- **THEN** `resolved_question` equals the written question

### Requirement: Recent-turn memory is budgeted behind evidence
When a conversation window is present, the system MAY include a rendered memory block (recent Q/A, optionally showing resolved questions) in the grounded composition prompt. That block SHALL fit under a configured token ceiling and SHALL be trimmed before truncating retrieved evidence. Memory text SHALL NOT be treated as a citation source.

#### Scenario: Memory fits under ceiling
- **WHEN** recent turns render under the memory token budget
- **THEN** the composer prompt includes that memory block
- **AND** citations still reference only retrieved corpus blocks

#### Scenario: Memory trimmed before evidence
- **WHEN** memory plus evidence would exceed the overall context policy
- **THEN** older memory turns are dropped first
- **AND** retrieved evidence is preferred over keeping memory turns

### Requirement: Rewrite audit is visible
When resolution substitutes one or more referents, the system SHALL expose that rewrite for operators (agent trace and/or response field such as substituted referents / resolved question), so a wrong expansion is detectable.

#### Scenario: Substituted referents listed
- **WHEN** resolution rewrites the question
- **THEN** the agentic outcome includes the resolved question (and substituted referents when applicable) in trace or payload metadata

### Requirement: No session means no memory behavior
Without a `session_id`, agentic runs SHALL not load a conversation window and SHALL not rewrite for memory; framing remains pass-through of the written question. Fact and anchor accumulation SHALL be a no-op without `session_id`.

#### Scenario: Agentic without session
- **WHEN** agentic start/sync omits `session_id`
- **THEN** no conversation window is loaded
- **AND** `resolved_question` equals the written question

### Requirement: Session accumulates conversation facts
When an agentic run is bound to a `session_id`, the system SHALL derive and merge structured conversation facts from the turn (at least domain when known and cited document identifiers when citations exist) without a dedicated LLM extraction call. Facts SHALL be available to subsequent turns in that session for resolution and memory rendering.

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
