# agentic-answer

## ADDED Requirements

### Requirement: No-evidence agentic answers abstain without invented procedures
When an agentic run has no retrieved evidence (`no_evidence` or empty hits), the composed answer SHALL be a short abstention that does not invent multi-step operational procedures, and the run SHALL remain eligible for human escalation per existing gate rules.

#### Scenario: Empty retrieve abstains
- **WHEN** corpus fetch yields no usable hits
- **THEN** the answer text is a brief insufficient-evidence message
- **AND** does not present a numbered operational procedure unsupported by citations
