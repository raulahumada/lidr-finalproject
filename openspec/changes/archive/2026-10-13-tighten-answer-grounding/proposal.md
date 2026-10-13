# Proposal: tighten-answer-grounding

## Why

Thin retrieval still yields long procedural answers that contradict the closing “insufficient evidence” hedge. Guardrails and eval need stricter abstention so Metropol answers do not invent handoff steps.

## What Changes

- Stronger v2 prompt rules against unsupported procedures
- Short-circuit abstention template when `no_evidence` / empty hits (no LLM)
- Optional review heuristic for long answers with few citations
- Prompt/fixture tests; docs (flush Redis if iterating same prompt version)

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rag-answer` and/or `agentic-answer`: abstention behavior when no evidence; grounded composition constraints

## Impact

- **Surface:** backend (`grounded_composer`, prompts v2, possibly gate)
- **Practices check:** domain agent + prompts; calibrate with golden set to avoid over-abstain
