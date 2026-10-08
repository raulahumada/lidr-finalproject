# Proposal

## Why

`POST /api/v1/answer` already works, but v1 prompts pass plain chunk lists and over-strict or under-structured grounding. That yields weak synthesis, empty citations, or refusals when evidence is partial. Course S9+ and peer lidr-master show that **visible provenance + token budget + numbered rules** improve grounded answers without new agents.

## What Changes

- Add Jinja `answer/v2` (system + user) with partial-answer rules and knowledge pack subordinated.
- Add a single context renderer: numbered blocks with stable ids (`chunk_id`) and `source_path` (course-style citability, peer-style readability).
- Fit retrieved hits to a token budget (drop whole chunks; no silent mid-chunk cut).
- Validate citation indices/ids against blocks actually sent; drop fabricated ones.
- Default `ANSWER_PROMPT_VERSION=v2` (keeps v1 selectable); document Redis flush when changing prompts mid-test.
- Tests for render, budget, citation filter; keep API contract stable (JSON answer + citations).

## Capabilities

### New Capabilities
- (none)

### Modified Capabilities
- `rag-answer`: stronger grounding via versioned prompts, budgeted context blocks, and citation validation.
- `knowledge-cag`: knowledge pack remains in system prompt under v2 rules (subordinated; no change to pack ceiling semantics).

## Impact

- **Surface:** backend.
- **Code:** `foundation/prompts/answer/v2/`, context builder under `generation/rag/`, `answer_service`, settings, tests, `AGENTS.md`.
- **Ops:** bumping prompt version changes exact-cache keys; optional `FLUSHDB` when iterating prompts locally.
- **Out of scope:** agents, multi-turn memory, XML-only course format, RAGAS evals.

## Practices check

- **Aligned:** prompts in `foundation/`; conductor in `domain/`; versioned templates; thin API; settings via `get_settings()`.
- **Deviations:** markdown numbered blocks instead of course XML `<source>` (same citability contract, simpler for Metropol Q&A); no Instructor re-prompt loop yet (filter bad citations in conductor).
- **Risks if ignored:** editing v1 in-place keeps stale cache semantics; unbounded context overflow; invented citation ids.
