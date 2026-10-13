# Proposal

## Why

The agentic Metropol answer API (`POST /answer/agentic` + resume) already ships on `development`, but operators still rely on curl for multi-step runs and human escalation. E1 only wired sync `/answer`. E2 closes the product loop: a console chat that shows the agent trace and supports approve / reject / adjust without leaving the Astryx shell.

## What Changes

- Upgrade `/answer` from the E1 single-shot form to an Astryx **`ai-chat`** transcript UI wired to the agentic API.
- Add a thin frontend client for agentic start + resume that treats **HTTP 202** as a deliberate pause (`awaiting_human_review`), not an error.
- Surface `agent_trace`, `review_reasons`, citations, and human-gate actions (approve / reject / adjust).
- Document MemorySaver caveat (paused `thread_id` lost on backend reload) for operators.
- Optionally keep sync `/answer` as a secondary toggle; agentic is the default path on `/answer`.

## Capabilities

### New Capabilities
- `agentic-chat-ui`: Operator console for agentic Metropol Q&A — transcript, agent trace, human escalation gate, and resume against the existing agentic answer API.

### Modified Capabilities
- `answer-chat-ui`: `/answer` remains the shell chat route, but the primary submit path becomes agentic; sync one-shot is optional/secondary rather than the sole contract.

## Non-goals

- Backend `/start` + progress polling, orchestrator hub, or Postgres checkpointer
- Changing agentic API contracts
- Next.js BFF proxy, auth, multi-turn conversation memory
- Hand-rolled layout CSS / Streamlit
- Copying peer shadcn or BFF relays verbatim

## Impact

- **Surface:** frontend only.
- **Code:** `frontend/app/answer/page.tsx` (scaffold `ai-chat`), `frontend/app/lib/api/` (agentic client), shell copy/nav if needed, `frontend/AGENTS.md`.
- **Reuse:** existing FastAPI agentic routes/schemas; `getApiBaseUrl` / error kinds from E1 sync client.
- **Deps:** `@heroicons/react` if the Astryx scaffold requires it.

## Graphify notes

- Hubs to consume (backend, unchanged): `AgenticAnswerRunner`, `answer_agentic` / `resume_agentic`, `AgenticAnswerResponse`.
- Hubs to extend (frontend): `answer/page.tsx`, `lib/api/answer.ts`, `AppShellLayout`.
- No directed front→agentic edge yet — this change creates the client bridge.
