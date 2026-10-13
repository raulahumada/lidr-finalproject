# Design

## Context

See proposal.md. Builds on `backend/eval/` and session-bound agentic runs. Peer: multiturn eval over the graph.

## Goals / Non-Goals

**Goals:** Measure follow-up rewrite + groundedness across turns with `session_id`.

**Non-Goals:** RAGAS; CI live gate; changing resolver heuristics (product change if fails).

## Decisions

1. **Separate CLI** `eval.run_multiturn` to keep 1-turn CLI simple.
2. **Expose `resolved_question`** on `AgenticAnswerResponse` (already in state).
3. **False negative:** `expect_rewrite=true` and resolved missing/equal to written → fail.
4. Create session per case; sequential agentic posts with `session_id`.

## Risks / Trade-offs

- [Flaky live LLM] → offline scorer tests; live opt-in with `--limit`
