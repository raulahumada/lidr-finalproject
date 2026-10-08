# knowledge-cag

## Purpose

Preloads a curated, bounded Metropol knowledge pack into the system prompt so the model always sees policy limits and stable context that retrieval alone may miss.

## ADDED Requirements

### Requirement: Curated pack in system prompt
The answer pipeline SHALL inject a curated knowledge pack into the system prompt used for generation (not the full corpus).

#### Scenario: Pack present when generating
- **WHEN** generation runs after a retrieval miss on caches and with evidence present
- **THEN** the system prompt includes the knowledge pack content

### Requirement: Token ceiling measured, never silent truncate
The pack size SHALL be measured with the same tokenizer family used for chunking. If the rendered pack exceeds the configured maximum tokens, loading/building SHALL fail explicitly; the system MUST NOT silently truncate the pack.

#### Scenario: Over ceiling fails loud
- **WHEN** the rendered pack token count exceeds the configured ceiling
- **THEN** an explicit error is raised (or startup/load fails)
- **AND** no truncated pack is used as if complete

### Requirement: Limits stated inside the pack
The pack SHALL include an in-band description of what it covers and what it does not, so the model does not treat absence from the pack as absence from the business.

#### Scenario: Limits section exists
- **WHEN** the knowledge pack is rendered
- **THEN** it contains a limits section describing coverage boundaries
