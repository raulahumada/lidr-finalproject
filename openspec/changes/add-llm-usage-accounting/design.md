# Design

## Context

See proposal.md — Why. Graphify hubs: `ChatClient.complete_json` (only OpenAI chat entry), callers `AnswerService`, `grounded_composer`, `prompt_specialist`; composition in `dependencies.py`; ORM/Alembic under `foundation/persistence`. Peer Cristian uses `RecordingLLM` + `Completion.usage`; course wrapper also accounts tokens (and estimates USD — out of scope). We have trusted BFF `X-Console-User` (unlike Cristian’s unauthenticated AI service).

## Goals / Non-Goals

**Goals:**
- Provider-reported tokens on every successful HTTP chat completion for answer paths
- Durable Postgres ledger queryable via summary API
- Admin UI to inspect aggregates
- Additive `usage` on answer HTTP bodies (last completion only)

**Non-Goals (design-level):**
- Changing how CAG / no_evidence skip the model (only how they report zeros)
- Replacing tiktoken context budgeting with billed usage
- Multi-provider adapters

## Decisions

1. **Extract usage inside `ChatClient`, persist via injected recorder**  
   `complete_json` reads OpenAI `usage.prompt_tokens` / `completion_tokens` / `total_tokens` into a small `Usage` value (or zeros + `reported=false`). Callers never touch the SDK. Recording is an optional callback / `UsageRecorder` protocol set at composition (HTTP path), so unit-test doubles stay dict-returning fakes.  
   *Alt A:* return `(dict, Usage)` everywhere — breaks many test fakes.  
   *Alt B:* SQLAlchemy inside `ChatClient` — violates foundation/llm ↔ persistence layer rule.  
   *Alt C:* full `RecordingLLM` wrapper class like Cristian — fine if preferred at apply time; same seam.

2. **Table `llm_usage_events` + store `record` / `summary`**  
   Columns: id, created_at, purpose, model, input/output/total tokens, reported, nullable session_id, thread_id, owner_id. Indexes on created_at, session_id, purpose.  
   *Alt:* only structlog — not queryable for console.  
   *Alt:* field on HistoryTurn — reject after gate never appends but was billed; mixes spend with provenance.

3. **Purposes:** `answer` | `grounded_composer` | `prompt_specialist`  
   Map 1:1 to call sites / ChatRole consumers.  
   *Alt:* single `answer` for all — loses agentic specialist breakdown.

4. **Record at call success; fail-open on insert**  
   Log `llm_usage_record_failed`; still return answer. Raised OpenAI errors → no row.

5. **HTTP `usage` = last completion of that run**  
   Multiple specialist calls → multiple ledger rows; body shows the last one. No call → zeros + `reported=false`. Summary `?session_id=` for totals.

6. **`owner_id` nullable from `X-Console-User`**  
   Trusted BFF only (already true for sessions). Summary is not filtered by owner by default (admin sees tenant-wide); optional future filter out of v1.

7. **`GET /api/v1/usage/summary`**  
   Totals + `by_model[]`; filters from/to/session_id/purpose; inverted range → 422. Protected by existing `SERVICE_TOKEN`. No USD.

8. **Frontend admin `/usage`**  
   Astryx page + BFF proxy; extend `ADMIN_ONLY` and `isAdminUpstreamPath` for `/usage` and `/api/v1/usage`. Filters mirror API. No money column.

## Layer map

| Piece | Layer |
|-------|--------|
| `Usage` + extract in `ChatClient` | foundation/llm |
| `UsageRecorder` / store | foundation/persistence |
| Alembic `llm_usage_events` | persistence |
| `schemas/usage.py` (+ answer `usage` field) | schemas |
| `api/routes/usage.py` | api (thin) |
| Wire recorder in `dependencies` | composition root |
| Pass purpose / ids at call sites | domain (`AnswerService`, agents) |
| Console `/usage` + BFF | frontend |

**Tension:** domain agents must not import the store; they call `ChatClient` (or a narrow protocol) that already has the recorder bound. Routers stay free of insert logic beyond the summary query via store.

## Risks / Trade-offs

- [Ledger outage loses rows] → Fail-open + warn; ops fix DB; answers continue  
- [Invented tokens] → Only provider fields; never tiktoken for ledger  
- [Eval / bare doubles skip ledger] → Intentional; production HTTP path records  
- [Admin summary is tenant-wide] → Acceptable single-tenant; `owner_id` stored for later filters  
- [CAG hit looks like “free” zeros on body] → Correct; `cached` already distinguishes sync path  

## Migration Plan

1. Alembic upgrade on local + Railway  
2. Deploy API (additive fields + new route)  
3. Deploy console `/usage`  
4. Rollback: drop route/UI; table can remain unused; old clients ignore `usage`

## Open Questions

None locked for apply (draft decisions accepted).
