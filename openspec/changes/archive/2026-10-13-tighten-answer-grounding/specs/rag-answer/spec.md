# rag-answer

## ADDED Requirements

### Requirement: Grounded prompts forbid unsupported procedures
Answer prompt templates SHALL instruct the model not to invent operational steps, endpoints, or policies that are not supported by retrieved excerpts, and to prefer short abstention or escalation language when evidence is insufficient.

#### Scenario: Prompt states no invented procedure
- **WHEN** the active answer prompt version is loaded
- **THEN** the system instructions include an explicit ban on inventing unsupported procedures and a preference for abstention when evidence is thin
