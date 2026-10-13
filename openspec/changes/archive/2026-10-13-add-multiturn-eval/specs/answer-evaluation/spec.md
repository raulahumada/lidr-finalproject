# answer-evaluation

## ADDED Requirements

### Requirement: Multiturn golden set evaluates follow-up resolution
The evaluation package SHALL include a multiturn golden set whose cases are ordered turns sharing a session. The harness SHALL create a conversation session, run each turn through sync agentic answer with that `session_id`, and score per-turn expectations including optional rewrite/`resolved_question` checks. A turn that expects a rewrite SHALL fail when `resolved_question` is missing or equal to the written question (false negative).

#### Scenario: Follow-up rewrite expected
- **WHEN** a multiturn case marks a turn with `expect_rewrite` true
- **AND** the agentic payload’s `resolved_question` is absent or equals the written question
- **THEN** that turn fails with a reason naming rewrite/resolution

#### Scenario: Session reused across turns
- **WHEN** a multiturn case has two or more turns
- **THEN** the harness uses the same `session_id` for each agentic call in that case
