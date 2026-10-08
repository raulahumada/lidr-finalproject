# response-cag

## Purpose

Caches previously generated answers so equivalent questions can be served without calling the LLM, using exact-match then semantic similarity lookups.

## Requirements

### Requirement: Exact-match cache before generation
The answer pipeline SHALL look up an exact-match cache keyed by a deterministic digest of the question plus generation-affecting parameters (at least prompt version, model, and k) before invoking the LLM, and SHALL return a cached payload on hit.

#### Scenario: Exact hit skips LLM
- **WHEN** an identical question and parameters were previously stored
- **AND** the answer pipeline runs again
- **THEN** the prior answer is returned
- **AND** `cached` reports an exact hit
- **AND** the LLM is not called

### Requirement: Semantic cache after exact miss
After an exact miss, the pipeline SHALL attempt a semantic cache lookup within a parameter bucket using embedding similarity at or above a configured threshold, unless log-only mode is enabled (lookup may still run for metrics but MUST NOT serve a hit).

#### Scenario: Log-only does not serve
- **WHEN** semantic cache log-only mode is enabled
- **AND** a near-duplicate question would otherwise match
- **THEN** generation proceeds as a miss for serving purposes

### Requirement: Store after successful generation
After a successful LLM generation (not a no-evidence short-circuit), the system SHALL store the answer in the exact cache and, when configured, the semantic cache.

#### Scenario: Miss then store
- **WHEN** both caches miss and generation succeeds
- **THEN** a subsequent exact lookup for the same inputs hits

### Requirement: Redis failure degrades to miss
Cache read/write failures SHALL NOT fail the request; the pipeline SHALL treat them as misses and continue generation when otherwise possible.

#### Scenario: Redis unavailable
- **WHEN** the cache backend is unreachable
- **AND** the LLM path is available
- **THEN** the request still completes with a generated (or no-evidence) answer
