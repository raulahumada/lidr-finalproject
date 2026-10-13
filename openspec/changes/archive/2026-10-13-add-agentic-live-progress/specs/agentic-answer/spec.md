# agentic-answer

## ADDED Requirements

### Requirement: Live progress endpoints are available alongside sync agentic
In addition to the synchronous `POST /api/v1/answer/agentic` path, the system SHALL expose background start and progress polling endpoints as defined by `agentic-live-progress`. The synchronous endpoint behavior SHALL remain unchanged.

#### Scenario: Sync path still completes
- **WHEN** a client posts to `POST /api/v1/answer/agentic` with a valid question and generation is configured
- **THEN** the response remains HTTP 200 or 202 with the existing agentic payload shape
