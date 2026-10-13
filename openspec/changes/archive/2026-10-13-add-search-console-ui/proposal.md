# Proposal: add-search-console-ui

## Why

Operators cannot inspect retrieval without paying for a full agentic answer. A `/search` console over the existing `POST /search` API makes corpus debugging and RAG demos transparent (roadmap E3 from the answer-chat draft; Cristian’s search console pattern).

## What Changes

- Frontend `/search` page + typed client + SideNav entry (Astryx)
- Optional `?q=` deep link
- Docs smoke in `frontend/AGENTS.md`
- No backend API changes

## Capabilities

### New Capabilities

- `search-console-ui`: operator UI to run semantic search and list scored hits

### Modified Capabilities

None.

## Impact

- **Surface:** frontend
- **API:** existing `POST /api/v1/search` (unchanged)
