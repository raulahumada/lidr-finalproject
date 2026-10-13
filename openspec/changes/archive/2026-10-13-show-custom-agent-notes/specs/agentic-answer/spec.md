# agentic-answer

## ADDED Requirements

### Requirement: Agentic outcomes expose custom agent notes
Agentic completed, paused, and rejected payloads SHALL include `custom_notes`: a list of objects with at least `key` (custom agent id) and `note` (text contribution). When no custom specialist ran, the list SHALL be empty.

#### Scenario: Notes present after custom ran
- **WHEN** an agentic run completes and graph state contains custom notes
- **THEN** the response includes those notes with matching keys and text

#### Scenario: Empty when no customs
- **WHEN** an agentic run completes with no custom notes in state
- **THEN** `custom_notes` is an empty list
