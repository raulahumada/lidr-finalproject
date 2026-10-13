# Tasks

## 1. Scaffold Astryx ai-chat

- [x] 1.1 From `frontend/`, run `npx astryx template ai-chat ./app/answer --overwrite` (or scaffold then merge into existing page) and install `@heroicons/react` if the scaffold imports it; verify `npm run build` (or `npm run dev` loading `/answer`) succeeds with the template frame intact
- [x] 1.2 Strip demo content from the scaffold while keeping ChatLayout / composer / message-list structure; verify the page still renders empty/composer state under the existing AppShell

## 2. Agentic API client

- [x] 2.1 Add typed `postAgenticAnswer` + `resumeAgenticAnswer` (extend `lib/api/answer.ts` or sibling module), reusing `getApiBaseUrl` and error kinds; verify 200 and **202** both return parsed `AgenticAnswerResponse` without throwing
- [x] 2.2 Map HTTP failures: 503 → unavailable, resume 404 → unknown thread, other non-OK / network → error; verify with mocked/status responses or a short unit/manual checklist documented in the PR notes

## 3. Wire chat UI + human gate

- [x] 3.1 Wire composer submit to agentic POST; render user turn, `agent_trace` steps, assistant answer, and citations (`source_path` + `excerpt`); verify a completed (HTTP 200) run shows answer + trace + citations when present
- [x] 3.2 Implement `awaiting_human_review` UI: show `review_reasons`, `thread_id` in metadata, and Approve / Reject / Adjust (Adjust sends edited answer); verify a paused run can resume and the UI reflects `completed` or `rejected`
- [x] 3.3 Loading and duplicate-submit/resume guards; verify in-flight actions are disabled and errors (503/404/network) show banners without fabricating answers
- [x] 3.4 Update shell/nav copy if needed so `/answer` reads as the Metropol answer chat (agentic-first); verify SideNav still highlights `/answer`

## 4. Docs + graph refresh

- [x] 4.1 Document agentic chat usage + MemorySaver caveat (paused threads lost on Uvicorn reload) in `frontend/AGENTS.md`; verify the doc mentions `NEXT_PUBLIC_API_BASE_URL` and the agentic/resume endpoints
- [x] 4.2 Run `graphify update .` from repo root after code lands; verify the command completes without error

## Workflow follow-up

- Archive change after apply + PR merge (`/opsx-archive` or project archive flow).
- Later: progress polling UI only if backend adds `/start` + progress; Postgres checkpointer is a separate backend change.
