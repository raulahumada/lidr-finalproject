# Proposal

## Why

Operators can create custom LLM agents and the graph already stores their `custom_notes`, but progress and chat hide them. Closing that gap makes the demo loop (create → run → see contribution) visible without guessing from routing alone.

## What Changes

- Expose `custom_notes` (`key` + `note`) on agentic response and progress payloads
- Map notes from graph state in the agentic runner
- Show notes on `/answer` during live progress and on terminal outcomes (Astryx)
- Short docs for operators

## Capabilities

### New Capabilities
<!-- none — extends existing agentic surfaces -->

### Modified Capabilities
- `agentic-answer`: terminal agentic payloads include `custom_notes`
- `agentic-live-progress`: progress payloads include accumulated `custom_notes` while running / at terminal
- `agentic-chat-ui`: chat UI surfaces custom agent notes when present

## Non-goals

- Persisting notes into session history
- Editing notes; changing ladder or citation rules
- Builtin personas / prompts

## Impact

- **backend:** `schemas/agentic_answer.py`, `domain/graph/runner.py`, tests
- **frontend:** `lib/api/agentic.ts`, `app/answer/page.tsx`, `frontend/AGENTS.md`
- **Graphify hubs:** `prompt_specialist`, `AgenticAnswerRunner._to_response`, `AnswerPageInner`

## Practices check

- **Aligned:** Pydantic DTOs; thin routes; runner maps state → response
- **Deviations:** none
- **Risks if ignored:** unbounded note length in UI — truncate display only
