# Design

## Context

See proposal.md — Why. Local package already has `resolver` + `budget` + `store`; peer has `facts`/`anchors` derived without LLM.

## Goals / Non-Goals

**Goals:** Durable Metropol facts + conservative ES scoping anchors; retrieval-first use; persist per session.

**Non-Goals:** Second LLM extract; UI; multiturn eval; Visual Time DB filters.

## Decisions

1. **Derive facts from turn outputs** (domain, cited document ids, light entity tokens) — peer pattern.
2. **Heuristic anchors only** for explicit scoping phrases; prefer miss over silent over-narrow.
3. **Persist** in session JSON/meta (Alembic only if model lacks a bag).
4. **Request `domain` override still wins** for the current call; session anchor biases when omitted.

## Risks / Trade-offs

- [False-positive anchor empties retrieve] → conservative regex; tests; never pin unknown filters that match nothing
