# agentic-chat-ui

## ADDED Requirements

### Requirement: Chat shows custom agent notes
When progress or a terminal agentic payload includes non-empty `custom_notes`, the `/answer` UI SHALL display each note’s agent key and text using Astryx components, without requiring the operator to inspect raw JSON.

#### Scenario: Live notes during run
- **WHEN** progress reports one or more custom notes while the run is in flight
- **THEN** the chat surface shows those notes to the operator

#### Scenario: Notes on completed run
- **WHEN** a terminal response includes custom notes
- **THEN** the notes remain visible with the assistant turn / audit area for that run
