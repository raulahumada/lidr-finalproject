# Proposal: polish-answer-chat-ui

## Why

`/answer` already surfaces answer text, custom notes, routing, tool calls, and citations on the same visual plane, so operators lose the grounded answer behind audit noise. Polishing hierarchy and collapsing the flow makes the Metropol demo scannable without new APIs.

## What Changes

- Reorder assistant turn content: **answer → custom notes → evidence → audit**
- Collapse routing + tool-call audit behind Astryx `Collapsible` (open while running; collapsed when terminal)
- Keep domain badge always visible when known
- Same content priority on history turns (notes above evidence; no empty audit block)
- Update `frontend/AGENTS.md` smoke notes

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agentic-chat-ui`: assistant-turn presentation order and collapsible audit behavior

## Impact

- **Surface:** frontend only
- **Code:** `frontend/app/answer/page.tsx`, `frontend/AGENTS.md`
- **API:** none
- **Graphify hubs:** `AnswerPageInner`, `CustomNotesList`, `runAgenticWithProgress` (consume-only)
