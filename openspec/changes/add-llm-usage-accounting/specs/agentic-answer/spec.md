# Spec Delta: agentic-answer

## ADDED Requirements

### Requirement: Agentic outcomes expose last-completion usage
Agentic completed, paused (`awaiting_human_review`), and rejected payloads SHALL include a `usage` object with `input_tokens`, `output_tokens`, `total_tokens`, and `reported`. When the run performed one or more chat completions, `usage` SHALL match the last successful completion of that run. When the run never called the model, `usage` SHALL be zeros with `reported=false`. Earlier completions in the same run remain on the ledger only.

#### Scenario: Completed run reports last composer usage
- **WHEN** an agentic run finishes grounded composition with reported total 140 and then completes without a second model call
- **THEN** the completed payload has `usage.total_tokens=140` and `usage.reported=true`

#### Scenario: Paused run still carries usage
- **WHEN** an agentic run synthesizes then pauses at the human gate
- **THEN** the paused payload includes `usage` from that synthesis completion

#### Scenario: No model call reports zeros
- **WHEN** an agentic run ends without calling the chat model
- **THEN** the payload `usage` has zero token fields and `reported=false`
