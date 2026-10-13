# Design

## Context

See proposal.md. Backend search already exists; frontend has AppShell + `/answer`/`/agents` but no `/search`.

## Goals / Non-Goals

**Goals:** Simple query form → hit list (score, path, excerpt); loading/empty/error.

**Non-Goals:** Ingest UI; ranking changes; auth; embedding search into chat.

## Decisions

1. Route `/search` + SideNav item.
2. Client `lib/api/search.ts` mirroring backend schemas.
3. Astryx List for hits; wrapping Text for excerpts.
4. Support `?q=` prefill + auto-search on load when present.

## Risks / Trade-offs

- [503 without OpenAI key] → same error pattern as answer chat
