# agentic-live-progress

## ADDED Requirements

### Requirement: Progress exposes accumulated custom notes
`GET .../progress` SHALL include `custom_notes` (same shape as agentic answer) reflecting notes accumulated so far. While status is `running`, notes MAY appear after the custom specialist has executed; terminal progress SHALL include the final list.

#### Scenario: Notes appear while running
- **WHEN** progress is polled after a custom specialist has written notes and status is still `running`
- **THEN** the progress payload includes those `custom_notes`

#### Scenario: Terminal progress carries notes
- **WHEN** progress reports a terminal status and notes exist in the run result
- **THEN** `custom_notes` is present on the payload
