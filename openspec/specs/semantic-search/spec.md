# semantic-search

## Purpose

Exposes semantic search over persisted RAG chunks so callers can retrieve the top-k most similar passages for a natural-language query, as the first retrieval surface before answer generation or agents.

## Requirements

### Requirement: Search endpoint under API prefix
The API SHALL expose `POST {api_prefix}/search` that accepts a JSON body with a non-empty `query` string and an integer `k` (bounded, with a documented default), and returns a typed response including the query, effective `k`, and a list of ranked results (chunk identity, content, score, and useful document metadata).

#### Scenario: Ranked results when corpus has embeddings
- **WHEN** the database contains chunks with embeddings and embeddings are configured
- **AND** a client calls `POST {api_prefix}/search` with a valid query and `k`
- **THEN** the response status is 200
- **AND** at most `k` results are returned ordered by similarity (best first)
- **AND** each result includes content and a numeric score

#### Scenario: Empty corpus is success with no hits
- **WHEN** embeddings are configured but no chunks with embeddings exist
- **AND** a client calls `POST {api_prefix}/search` with a valid query
- **THEN** the response status is 200
- **AND** `results` is an empty list

#### Scenario: Invalid k is rejected
- **WHEN** a client calls `POST {api_prefix}/search` with `k` outside the allowed bounds
- **THEN** the response status is 422

### Requirement: Clear failure when embeddings unavailable
If the embeddings provider is not configured, search SHALL fail with a clear service-unavailable response rather than returning invented rankings.

#### Scenario: Missing embeddings configuration
- **WHEN** the embeddings API key (or equivalent required config) is not set
- **AND** a client calls `POST {api_prefix}/search`
- **THEN** the response status is 503
- **AND** the body indicates the embedding service is not available

### Requirement: Thin HTTP boundary
Search request handling SHALL keep embedding and ranking logic outside the router (service/retriever layer), so HTTP handlers only validate input, map status codes, and return the typed response model.

#### Scenario: Contract visible in OpenAPI
- **WHEN** a developer opens the API docs
- **THEN** `POST {api_prefix}/search` appears with request and response schemas
