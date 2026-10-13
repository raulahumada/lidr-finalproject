# Design

## Context

See proposal.md — Why. Graphify hubs for the chat path are `answer/page.tsx`, `agentic.ts`, and `AgenticAnswerRunner` / `answer_agentic`. Persistence already uses Postgres via `get_session_factory`. Course `generation/conversation/` is in-process; peer lidr-master persists `conversation_sessions` with JSON `history` and separate list/detail routes. LangGraph `thread_id` (Postgres checkpointer) remains one graph run; sessions must not live inside the checkpointer.

## Goals / Non-Goals

**Goals:**
- Durable multi-session transcripts in Postgres.
- Thin session CRUD API + optional `session_id` on agentic start/sync.
- `/answer` UI: list, create, switch, restore via `?session=`, Astryx-only layout.

**Non-Goals:**
- Prompt-time session memory (facts/anchors).
- Auth-scoped ownership.
- Activity-log durability.

## Decisions

### 1. `session_id` ≠ `thread_id`
**Choice:** Session spans many agentic runs; each run still gets its own `thread_id` for progress/resume.

**Alternatives:** One checkpointer thread per chat — rejected (peer/`store.py` rationale: session memory ≠ graph pause state).

### 2. Module placement (layers)
| Piece | Layer |
|-------|--------|
| ORM + Alembic | `foundation/persistence` |
| `SessionStore` | `generation/conversation/` (course-shaped) |
| Pydantic contracts | `schemas/` |
| HTTP | `api/routes/answer_session.py` (+ list router) |
| Append on terminal | called from agentic routes/runner conductor, not from specialist nodes |

**Tension:** Course store is in-memory; we persist like peer. Acceptable.

### 3. History JSONB on one row
**Choice:** `conversation_sessions` with `history` JSONB (and title, timestamps), peer-like.

**Alternatives:** Normalized `conversation_turns` table — better for analytics later; deferred for v1 speed.

### 4. When to append
**Choice:** Append after terminal **completed**, **rejected**, or successful **adjust** resume (and sync 200 completed). Include `status`, `thread_id`, question, answer, citation snapshots. Do **not** append while `awaiting_human_review` or `running`.

**Auto-title:** First question truncated if title empty.

### 5. Frontend
**Choice:** Extend `frontend/app/answer/page.tsx` with Astryx patterns from `npx astryx template ai-chat` (Toolbar / list / ChatLayout). Deep link `?session=`. New `lib/api/sessions.ts`; pass `session_id` into start/poll helpers.

**Alternatives:** Scaffold `src/app/ai-chat` — rejected; conflicts with existing App Router `/answer`.

### 6. Auth
**Choice:** Single-tenant list (all sessions). Document follow-up for `owner_id`.

## Risks / Trade-offs

- [JSONB history growth] → Cap turns per session or document limit; trim oldest only if needed later.
- [Append races on concurrent tabs] → Last-write-wins on JSON array; acceptable for demo.
- [Unknown session_id on start] → 404 before scheduling run.
- [UI without Astryx] → Forbidden by frontend AGENTS; use template components.

## Migration Plan

1. Alembic create `conversation_sessions`.
2. Ship API + agentic wiring; UI behind same `/answer`.
3. Rollback: drop table / revert migration; agentic without `session_id` unchanged.

## Open Questions

None — draft open questions resolved in Decisions (append rejects, auto-title, no LLM memory in v1).
