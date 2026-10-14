# Tasks

## Backend

## 1. Usage value + ChatClient extraction

- [x] 1.1 Add a small `Usage` (or equivalent) type with `input_tokens`, `output_tokens`, `total_tokens`, `reported` near `foundation/llm` — verify: unit test or type import without OpenAI SDK.
- [x] 1.2 Extend `ChatClient.complete_json` to extract OpenAI `usage` (or zeros + warn `llm_usage_missing`) without inventing tokens — verify: `pytest` with mocked completion that has / lacks `usage`.
- [x] 1.3 Add optional `UsageRecorder` (or callback) injected into `ChatClient` / composition so successful completions can record without importing SQLAlchemy inside llm — verify: recorder called on success, not on raised errors; tests keep plain doubles.

## 2. Ledger persistence

- [x] 2.1 Add ORM model + Alembic migration for `llm_usage_events` (purpose, model, tokens, reported, nullable session_id/thread_id/owner_id, created_at + useful indexes) — verify: `alembic upgrade head` locally creates the table.
- [x] 2.2 Implement store `record` (fail-open caller responsibility) and `summary` (totals + by_model, filters from/to/session_id/purpose; inverted range validation at API) — verify: store unit tests with a test DB or transactional fixture.

## 3. Wire answer paths

- [x] 3.1 Compose recorder in `dependencies.py` for sync + agentic chat clients; pass purpose `answer` / `grounded_composer` / `prompt_specialist` and available session/thread/owner ids at call sites — verify: integration/API tests assert one ledger row per successful completion purpose.
- [x] 3.2 Ensure skipped model paths (no_evidence, CAG hit, empty fit) write **no** row — verify: existing answer tests + new assertion on ledger count.
- [x] 3.3 Add `usage` to sync `AnswerResponse` and agentic completed/paused/rejected/progress payloads (last completion; zeros when none) — verify: API tests on `/answer`, agentic sync, and `/progress`.

## 4. Summary API

- [x] 4.1 Add schemas + thin `GET /api/v1/usage/summary` router (SERVICE_TOKEN as other routes) — verify: empty window → zeros; inverted from/to → 422; seeded rows → totals + by_model.
- [x] 4.2 Document endpoint briefly in `backend/README.md` or AGENTS usage curl snippet — verify: docs mention summary path and that ledger is Postgres.

## Frontend

## 5. BFF + admin gates

- [x] 5.1 Add same-origin BFF route that proxies usage summary with service token — verify: handler requires session; returns upstream JSON/errors.
- [x] 5.2 Extend `ADMIN_ONLY` with `/usage` and `isAdminUpstreamPath` for `/api/v1/usage` — verify: unit test or role helper coverage; usuario denied.

## 6. Usage console UI

- [x] 6.1 Build admin `/usage` page with Astryx (totals + by_model table; filters from/to/purpose/session_id; no USD) — verify: page renders with mocked summary; 422 keeps prior totals and shows error.
- [x] 6.2 Link `/usage` in SideNav (admin-visible) — verify: nav entry present for administrador flows.

## 7. Integration check

- [x] 7.1 Run backend `pytest -q` focused on usage/answer/agentic; smoke frontend lint/build for touched files — verify: green locally.
- [x] 7.2 After merge/apply: run `graphify update .` so the knowledge graph picks up ChatClient/recorder/usage route — verify: `graphify-out/graph.json` refreshes without error.
