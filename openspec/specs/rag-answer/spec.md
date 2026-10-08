# rag-answer

## Purpose

Provides grounded natural-language answers over the Metropol Fintech corpus by retrieving evidence, generating with an LLM, and returning citations.

## Requirements

### Requirement: Answer endpoint accepts a question
The system SHALL expose `POST /api/v1/answer` that accepts a non-empty question and optional `k`, and returns an answer payload including text, citations, cache status, prompt version, and latency.

#### Scenario: Successful grounded answer
- **WHEN** embeddings and chat are configured and relevant chunks exist
- **AND** a client posts a question
- **THEN** the response includes a non-empty answer string
- **AND** citations reference retrieved sources when evidence was used
- **AND** `cached` indicates whether a response cache served the result

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
