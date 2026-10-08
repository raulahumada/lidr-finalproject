# knowledge-cag

## MODIFIED Requirements

### Requirement: Curated pack in system prompt
The answer pipeline SHALL inject a curated knowledge pack into the system prompt used for generation (not the full corpus). Under prompt version v2 and later, the pack SHALL remain subordinated to retrieval-grounding rules (it MUST NOT authorize inventing facts absent from retrieved evidence and the pack itself).

#### Scenario: Pack present when generating
- **WHEN** generation runs after a retrieval miss on caches and with evidence present
- **THEN** the system prompt includes the knowledge pack content

#### Scenario: Pack does not override missing evidence
- **WHEN** retrieval returns no chunks
- **THEN** the no-evidence path still applies without using the pack to invent corpus facts
