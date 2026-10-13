# Design

## Context

See proposal.md. Hubs: `grounded_composer`, knowledge pack, `review_reasons`/`no_evidence`.

## Goals / Non-Goals

**Goals:** Short deterministic abstention without evidence; discourage invented procedures when evidence is partial.

**Non-Goals:** RAGAS; retrieve changes; facts/anchors; prompt v3 bump unless required.

## Decisions

1. **No-LLM short-circuit** on empty hits / `no_evidence` in composer (agentic + keep sync path consistent if shared).
2. **Iterate `ANSWER_PROMPT_VERSION=v2`** + document Redis flush; no v3 unless CAG keying forces it.
3. **Light heuristic optional:** long answer + few citations → lower confidence or extra review reason.

## Risks / Trade-offs

- [Over-abstain] → golden/eval smoke on real Metropol questions
