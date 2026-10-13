# Design

## Context

See proposal.md — Why. `prompt_specialist` already appends `custom_notes` to LangGraph state and `grounded_composer` injects them into the prompt. `AgenticAnswerRunner._to_response` and progress assembly omit that field. Frontend already shows `routing_history` / `agent_trace`.

## Goals / Non-Goals

**Goals:**
- Typed `custom_notes` on agentic answer + progress DTOs
- Chat visibility live + terminal

**Non-Goals:**
- Session transcript persistence; note editing

## Decisions

### 1. Single field on existing payloads
**Choice:** Add `custom_notes: list[{key, note}]` to `AgenticAnswerResponse` and `AgenticProgressResponse` (default `[]`).

**Alternatives:** Only embed in `agent_trace` — rejected (trace already has summaries; structured notes are clearer for UI).

### 2. Progress includes partial notes while running
**Choice:** When mapping progress from activity log / checkpoint values, copy `custom_notes` from current graph values if present.

### 3. UI placement
**Choice:** On `/answer`, next to routing: a compact List “Aportes custom” when `custom_notes.length > 0` (live state + result). Truncate long notes in the UI (~400 chars) with full text still in API.

### 4. No history append
**Choice:** Session turns unchanged this change (avoids schema/migration for transcript).

## Risks / Trade-offs

- [Empty notes after failed specialist] → still show empty list; UI hides section
- [Very long notes] → UI truncate; optional schema max later

## Migration Plan

1. Deploy schema + runner (backward compatible: new optional field).
2. Ship frontend consumers.
3. Rollback: ignore unknown field on old clients.

## Open Questions

None — draft defaults locked.

## Practices check

Schemas in `app/schemas`; mapping only in runner; no business logic in routes.
