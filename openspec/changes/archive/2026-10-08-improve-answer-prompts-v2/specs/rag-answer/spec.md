# rag-answer

## MODIFIED Requirements

### Requirement: Answer endpoint accepts a question
The system SHALL expose `POST /api/v1/answer` that accepts a non-empty question and optional `k`, and returns an answer payload including text, citations, cache status, prompt version, and latency. When generation runs, the active prompt version SHALL assemble retrieved evidence into discrete context blocks that expose a stable id and source path so citations can be verified.

#### Scenario: Successful grounded answer
- **WHEN** embeddings and chat are configured and relevant chunks exist
- **AND** a client posts a question
- **THEN** the response includes a non-empty answer string
- **AND** citations reference retrieved sources when evidence was used
- **AND** `cached` indicates whether a response cache served the result
- **AND** `prompt_version` reflects the template version used for an uncached generation

#### Scenario: Context blocks carry provenance
- **WHEN** generation runs with one or more retrieved hits
- **THEN** the user prompt includes numbered (or otherwise discrete) blocks each showing a stable evidence id and source path

### Requirement: Missing API key yields 503
When the OpenAI API key is not configured, the answer endpoint SHALL respond with HTTP 503 rather than calling the LLM.

#### Scenario: No API key
- **WHEN** `OPENAI_API_KEY` is empty
- **AND** a client posts to `/answer`
- **THEN** the status code is 503

### Requirement: No evidence without inventing
When retrieval returns no chunks, the system SHALL return a clear no-evidence answer without calling the LLM, and SHALL NOT invent policy or facts.

#### Scenario: Empty retrieval
- **WHEN** search yields zero chunks for the question
- **THEN** the answer states that there is insufficient evidence in the corpus
- **AND** citations are empty
- **AND** the LLM is not invoked

### Requirement: Partial answers when evidence is incomplete
When some retrieved evidence supports part of the question but not all of it, the system SHALL allow the model (via prompt policy) to answer the supported part and explicitly mark what is missing, rather than refusing entirely or inventing the gap.

#### Scenario: Partial support
- **WHEN** retrieved blocks support only part of the question
- **AND** generation runs
- **THEN** the answer may include both supported claims and an explicit insufficiency statement for the unsupported part

### Requirement: Citations must refer to sent evidence
The system SHALL drop citation references that do not correspond to evidence blocks included in the prompt for that generation.

#### Scenario: Fabricated citation dropped
- **WHEN** the model returns a citation id or index not present in the sent context blocks
- **THEN** that citation is omitted from the API response

### Requirement: Retrieved context respects a token budget
Before prompting, the system SHALL fit retrieved hits into a configured token budget by dropping whole chunks (least preferred first), without silently truncating the middle of a kept chunk’s block text for budgeting purposes.

#### Scenario: Over-budget drops whole chunks
- **WHEN** wrapped context blocks would exceed the configured answer context token budget
- **THEN** one or more trailing/least-preferred hits are omitted entirely
- **AND** remaining blocks are sent intact
