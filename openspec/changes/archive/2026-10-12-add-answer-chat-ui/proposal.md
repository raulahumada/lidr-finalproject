# Proposal

## Why

Backend already exposes grounded Metropol Q&A via `POST /api/v1/answer`, but the Next.js shell has no product surface that calls it. Without a chat page, operators still use curl/`/docs`. This change ships the first UI slice: sync ask → answer + citations on Astryx.

## What Changes

- Add a chat route (proposed `/answer`) inside the existing Astryx `AppShell`.
- Add a thin typed frontend client for `POST /api/v1/answer` (question, optional `k`).
- Render idle / loading / success (answer + citations) / error (incl. 503) states with Astryx components.
- Wire `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:8000`) and document it.
- Extend side nav with a link to the chat route.

## Capabilities

### New Capabilities
- `answer-chat-ui`: Sync Metropol answer chat in the frontend — form, API client, answer + citations display, error handling — consuming the existing `rag-answer` API.

### Modified Capabilities
- (none — `rag-answer` / `agentic-answer` requirements stay; this change only consumes sync `/answer`)

## Non-goals

- Agentic mode, human resume, agent trace, progress polling (deferred to `add-agentic-chat-ui`)
- Multi-turn session history / auth
- Search console, ingest preview, admin corpus
- Backend API changes
- Replacing Astryx with custom `<div>` layouts or peer shadcn verbatim

## Impact

- **Surface:** frontend only.
- **Code:** `frontend/app/answer/` (or equivalent), `frontend/app/lib/api/` thin client, `app-shell.tsx` nav, `.env.example` / docs; backend untouched.
- **Reuse:** existing `AppShellLayout`, Astryx kit + stone theme; contract from `AnswerRequest` / `AnswerResponse` (`schemas/answer.py`).
- **CORS:** backend already allows `localhost:3000` by default; verify when testing.

## Graphify notes

- Frontend hubs: `AppShellLayout()`, `layout.tsx`, `app/page.tsx`.
- Backend contract hubs (consume only): `answer()`, `AnswerService`, `AnswerResponse`.
- No new backend island; chat UI extends the shell nav island.
