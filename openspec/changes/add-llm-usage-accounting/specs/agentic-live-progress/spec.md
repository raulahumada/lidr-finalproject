# Spec Delta: agentic-live-progress

## ADDED Requirements

### Requirement: Progress exposes last-completion usage
`GET /api/v1/answer/agentic/{thread_id}/progress` SHALL include a `usage` object with `input_tokens`, `output_tokens`, `total_tokens`, and `reported`. Progress SHALL expose the last successful chat completion of the run when one exists; otherwise zeros with `reported=false`. Terminal progress SHALL stay consistent with agentic outcome usage rules.

#### Scenario: Early progress has zero usage
- **WHEN** a background run is still `running` and no specialist has completed a chat call
- **THEN** progress includes `usage` with zeros and `reported=false`

#### Scenario: Terminal progress matches last usage
- **WHEN** a background run reaches `completed` after a reported completion totaling 140 tokens
- **THEN** progress includes `usage.total_tokens=140` and `usage.reported=true`
