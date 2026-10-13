# Tasks

## 1. Backend activity + start/progress

- [x] 1.1 Add `domain/graph/activity.py` (`GraphActivityLog` + `describe_node` for Metropol nodes) and verify unit tests cover known nodes and unknown-node degrade
- [x] 1.2 Extend `AgenticAnswerRunner` with background `graph.stream` thread + activity finish states; verify a background run reaches completed or awaiting_human_review in the activity log
- [x] 1.3 Add schemas + routes `POST /answer/agentic/start` and `GET /answer/agentic/{thread_id}/progress` with deps wiring; verify API tests for 202 start, poll terminal, 404, and sync POST still green
- [x] 1.4 Document start/progress curl examples and process-scoped caveat in root `AGENTS.md`; verify commands match routes

## 2. Frontend poll UI

- [x] 2.1 Add `startAgenticAnswer`, `getAgenticProgress`, and poll helper in `lib/api/agentic.ts`; verify 202 start parse and progress polling types compile
- [x] 2.2 Wire `/answer` to start+poll with live `ChatToolCalls` step states; verify completed and awaiting_human_review paths still show answer/gate
- [x] 2.3 Update `frontend/AGENTS.md` for start+poll; verify docs mention poll interval and MemorySaver/progress 404 caveat

## 3. Graph refresh

- [x] 3.1 Run `graphify update .` after code lands; verify command succeeds

## Workflow follow-up

- Archive after PR merge.
- Later: Redis activity / Postgres checkpointer if multi-worker.
