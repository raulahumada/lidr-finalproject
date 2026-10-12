# Design

## Context

See proposal.md — Why. Frontend already has Astryx 0.6.8 + stone theme, `AppShellLayout` (nav: Inicio / Items / Ajustes), and no HTTP client to the API. Backend `POST /api/v1/answer` returns `AnswerResponse` (`question`, `answer`, `citations[]`, `cached`, `prompt_version`, `k`, `latency_ms`, `no_evidence`) and 503 without `OPENAI_API_KEY`.

Graphify: extend `AppShellLayout` / `layout.tsx`; consume `answer()` / `AnswerResponse` — do not invent a second shell or shared monorepo package.

## Goals / Non-Goals

**Goals:**
- One sync chat page under the existing shell that posts to `/api/v1/answer` and shows answer + citations.
- Configurable API base URL for local/dev.
- Astryx-first UI (template → components), no raw layout CSS islands.

**Non-Goals:**
- Agentic / resume UI (E2).
- Shared TypeScript package with backend schemas.
- Streaming, multi-turn memory, auth.

## Decisions

### 1. Route `/answer`
Aligns with API and peer console naming. Alternative `/chat` deferred; nav label can still say “Respuesta” / “Chat”.

### 2. Thin client `frontend/app/lib/api/answer.ts` (or `frontend/lib/api/`)
`fetch` + mirrored types for request/response/citation. Base URL from `process.env.NEXT_PUBLIC_API_BASE_URL` defaulting to `http://localhost:8000`. No React Query / SWR in E1 unless already present (it is not).

### 3. Astryx template starting point
`astryx build` maps this idea to **`ai-chat`** (transcript + composer) or **`ai-chat-landing`** (zero-state composer). Prefer **`ai-chat-landing`** for E1 (single-shot Q&A, no history), or scaffold `ai-chat` and collapse history to one user + one assistant turn. Keep template frame/gap; replace content. May need `@heroicons/react` if the template imports it — install only if scaffold requires it. Read props via `astryx component` before wiring TextArea / Button / List / Heading / Text / Banner (errors).

### 4. Client page + local state
`"use client"` page (or client child) with idle → loading → success | error. Disable submit while loading. Show `no_evidence` and citation `source_path` + `excerpt` (score optional). Do not call agentic endpoints.

### 5. Nav only — no second layout
Add SideNavItem under Principal pointing at `/answer`; `isSelected` via `usePathname` like Items/Settings.

### 6. Env + docs
`frontend/.env.example` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`; mention in `frontend/AGENTS.md` or root `AGENTS.md` frontend section briefly.

## Risks / Trade-offs

- **[CORS / wrong base URL]** → Document default; verify backend CORS includes `:3000`; surface network errors in UI.
- **[503 without OpenAI key]** → Map status to a clear Banner/Text; do not pretend success.
- **[ai-chat template heavier than needed]** → Prefer landing / minimal form if transcript chrome fights single-shot UX; still no hand-rolled div layout.
- **[Stale types if API drifts]** → Keep types next to client; E1 accepts manual sync with `schemas/answer.py`.

## Migration Plan

- Additive frontend only; no backend deploy coupling beyond running API locally.
- Rollback: remove route + nav link + client module.

## Open Questions

- None blocking apply (route `/answer` and sync-only E1 decided in draft).
