# Proposal: add-multiturn-eval

## Why

Single-turn eval cannot catch resolver false negatives on follow-ups (“¿y con Tenela?”). Cristian measured that next; Metropol already has 1-turn harness and session memory — extend measurement to multi-turn sequences through the agentic path.

## What Changes

- Golden multiturn set + scorer for rewrite/resolved expectations
- CLI `python -m eval.run_multiturn` (session loop + optional auto-approve)
- Expose `resolved_question` on agentic response for scoring/debug
- Offline tests; docs in `AGENTS.md`

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `answer-evaluation`: multiturn golden harness and rewrite/false-negative checks
- `agentic-answer`: response MAY/SHALL include `resolved_question` when resolution ran

## Impact

- **Surface:** backend
- **Graphify:** `eval/*`, `resolve`, agentic schemas/runner
- **Practices check:** eval outside `app/`; pure scorer; live opt-in only
