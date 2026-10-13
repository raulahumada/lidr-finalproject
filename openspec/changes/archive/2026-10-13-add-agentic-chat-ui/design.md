# Design

## Context

See `proposal.md` for motivation. Backend agentic API and schemas already exist (`answer_agentic`, `resume_agentic`, `AgenticAnswerResponse`). Frontend E1 owns `/answer` as a sync form (`answer/page.tsx` + `lib/api/answer.ts`) inside `AppShellLayout`. Graphify shows no front→agentic edge yet; hubs to extend are the answer page, API client, and shell — consume `AgenticAnswerRunner` community only via HTTP.

Course UI reference is a thin HTTP client (Streamlit estimate form). Peer console uses `/start` + progress polling and a Next BFF; we call FastAPI directly and use the blocking agentic POST (200/202), matching our API v1.

## Goals / Non-Goals

**Goals:**
- Scaffold Astryx `ai-chat` into `/answer` and wire agentic start + human resume.
- Treat 202 as pause; show trace, reasons, citations; expose `thread_id` in metadata.
- Reuse E1 base URL and error-kind patterns; keep surface frontend-only.

**Non-Goals:**
- Progress polling, BFF relays, backend checkpointer/orchestrator changes.
- Multi-turn conversational memory across agentic runs.
- Pixel-perfect peer/shadcn clone.

## Decisions

1. **Template: `ai-chat` over `ai-chat-landing`**  
   E2 needs transcript + tool/trace chrome; `astryx build` maps the idea to `ai-chat`. Landing stays a fallback only if scaffold chrome fights the gate UX. Install `@heroicons/react` if the scaffold imports it. Keep template frame/gap; replace demo content.

2. **Same route `/answer`, agentic default**  
   Avoid a second nav item. Sync remains optional secondary toggle if cheap; otherwise leave sync client in `lib/api` unused by the default composer. Spec `answer-chat-ui` updated so sync is MAY, not the sole MUST.

3. **Client shape**  
   Extend `lib/api/answer.ts` or add sibling `lib/api/agentic.ts` exporting `postAgenticAnswer` / `resumeAgenticAnswer` + types mirrored from `schemas/agentic_answer.py`. Critical: parse JSON on **200 and 202**; only throw `AnswerApiError` for true failures (network, 503, 404, other non-OK).

4. **UI state machine**  
   `idle → loading → (completed | awaiting_review | rejected | error)`. Review panel renders when status is `awaiting_human_review`; resume transitions back through loading. Map `agent_trace` to ChatSystemMessage / ChatToolCalls-style rows; citations via Astryx `Citation` or List/Item under the assistant turn / artifact panel — choose after inspecting scaffold.

5. **No BFF**  
   Browser → FastAPI with CORS already allowing localhost:3000 (same as E1). Peer BFF deferred.

6. **MemorySaver caveat**  
   Document in `frontend/AGENTS.md` (+ short Banner/helper text on 404 resume): paused threads die on Uvicorn reload. No backend change in this slice.

## Risks / Trade-offs

- **[Risk] Operators confuse 202 with failure** → Client must treat 202 as success-pause; UI copy “Revisión humana” not “Error”.
- **[Risk] `ai-chat` scaffold heavier than needed** → Strip unused artifact/demo pieces; keep ChatLayout + composer + message list.
- **[Risk] Lost threads after reload** → Document MemorySaver; surface 404 clearly.
- **[Trade-off] Blocking POST vs peer live progress** → Accept longer spinner; progress API is a later backend change.
- **[Trade-off] Overwriting E1 form** → Agentic is the product path; sync optional. Rollback = revert page to previous form.

## Migration Plan

1. Scaffold `ai-chat` into `frontend/app/answer` (overwrite with care).
2. Add agentic client + wire states / gate.
3. Smoke: completed path + forced low-confidence pause → resume approve.
4. Update front AGENTS docs; run `graphify update .` after apply.

Rollback: restore prior `answer/page.tsx` + sync-only client usage; API unchanged.

## Open Questions

None blocking apply — artifact vs inline citations decided during scaffold inspection.
