# Proposal: add-conversation-facts-anchors

## Why

Session memory today is a short turn window plus a conservative resolver. Follow-ups still lose durable scope (“solo cobranzas”) and cited entities when the window rolls. Cristian’s peer closes that with facts + anchors feeding retrieval first; Metropol deferred that slice and needs it next.

## What Changes

- Add peer-shaped `facts.py` / `anchors.py` / models under `generation/conversation/` (no second LLM for extraction)
- Persist and merge session facts/anchors; inject into resolver, light retrieve bias, and `render_memory` (evidence wins)
- Unit tests + `AGENTS.md` memory model update

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `conversation-memory`: session facts and scoping anchors participate in resolve/retrieve/memory block

## Impact

- **Surface:** backend
- **Graphify:** `resolve`, `render_memory`, `SessionStore`, `intent_framer`
- **Practices check:** aligned with conversation layer + conductor; Metropol vocabulary ≠ Visual Time (conscious); risk = false-positive anchors emptying retrieve
