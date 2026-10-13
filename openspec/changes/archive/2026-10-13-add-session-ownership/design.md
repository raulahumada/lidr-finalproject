# Design

## Context

See proposal.md — Why. Today `SessionStore.list_summaries` / `get` / `delete` have no owner filter (`ConversationSessionRow` has no `owner_id`). Graphify hubs: `SessionStore`, `answer_session.py`, `answer_agentic.py` (`_require_session` / append). The Next BFF (`relay.ts`) already sets `X-Console-User` from Auth.js `session.user.id` (max 64 chars via `consoleUserHeaderFor`).

## Goals / Non-Goals

**Goals:**
- Stamp and enforce per-console-user ownership on conversation sessions
- Keep scripts/eval usable without the header (unowned rows only)
- Fail closed for cross-user access without leaking existence via 403

**Non-Goals:**
- Admin global session browser
- Assigning historical null rows to users
- Checkpointer / `thread_id` isolation

## Decisions

1. **Column `owner_id` on `conversation_sessions` (nullable String(64))**  
   Same id space as Auth.js user id / BFF header. Index for list-by-owner.  
   *Alt:* separate ownership table — rejected; one row per session is enough.

2. **Header `X-Console-User` as the sole owner signal**  
   FastAPI `Depends` (or small helper in `api/`) reads it; empty/missing → `None`. Over-long values dropped (parity with BFF).  
   *Alt:* pass owner in JSON body — rejected; spoofable from any client that already has the service token less cleanly, and BFF already has the header path.

3. **Scope rules**

   | Caller | Create | List / get / mutate / agentic session use |
   |--------|--------|-------------------------------------------|
   | Header present | `owner_id = header` | Only rows with `owner_id == header` |
   | No header | `owner_id = null` | Only rows with `owner_id IS NULL` |

   Console users therefore never see legacy/unowned sessions. Scripts without header stay in the null bucket.

4. **404 not 403 on mismatch**  
   Same detail as unknown `session_id` — avoids confirming another user’s id exists.

5. **Enforce in `SessionStore` + routers**  
   Store methods take `owner_id: str | None` (expected scope). Routers pass `get_console_user_id`. Agentic `_require_session` / append paths use the same check so a stolen `session_id` cannot append under another owner.  
   *Alt:* filter only in list — rejected; get-by-id would still leak transcripts.

6. **Layer map** (python-best-practices)

   | Piece | Layer |
   |-------|--------|
   | Alembic + `ConversationSessionRow.owner_id` | foundation/persistence |
   | `SessionStore` filter/stamp | generation/conversation |
   | Header Depends | api |
   | Session + agentic routes | api (thin) |

## Risks / Trade-offs

- [Open mode without `SERVICE_TOKEN`: spoofed `X-Console-User`] → Mitigation: document; locked mode requires Bearer; same trust model as other routes today
- [Existing sessions become invisible in the console] → Mitigation: expected; operators recreate chats; null rows remain for curl/eval
- [Eval harness creating sessions without header] → Mitigation: stays in null bucket; document if a test needs a fake header

## Migration Plan

1. `alembic upgrade` adds nullable `owner_id` (existing rows null)
2. Deploy API that scopes by header
3. Console (via BFF) immediately creates owned sessions
4. Rollback: drop filter code; column can remain unused

## Open Questions

None (draft defaults locked).
