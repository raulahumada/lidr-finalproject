# Tasks

## 1. Env and API client

- [x] 1.1 Add `frontend/.env.example` with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` and a short note in `frontend/AGENTS.md` (or root `AGENTS.md` frontend section); verify the documented default matches the client fallback
- [x] 1.2 Create thin typed client `frontend/app/lib/api/answer.ts` (types mirrored from `AnswerRequest` / `AnswerResponse` / `Citation`) that posts to `{base}/api/v1/answer` and maps non-OK responses (incl. 503) to a clear error; verify with a unit-style call mock or a manual curl-aligned smoke against a running API

## 2. Chat page (Astryx)

- [x] 2.1 Run `npx astryx build` / scaffold from `ai-chat-landing` (or `ai-chat` if landing is insufficient) into `frontend/app/answer/`; keep template frame; verify route builds (`npm run build` or `npm run dev` loads `/answer`)
- [x] 2.2 Wire form (question + optional `k`), loading/disabled submit, success (answer + citation list with `source_path` / `excerpt`), and error Banner for 503/network; verify idle → loading → success/error manually against backend
- [x] 2.3 Handle `no_evidence` / empty citations without inventing citation rows; verify with a question that yields no corpus hits (or mocked empty citations)

## 3. Shell nav

- [x] 3.1 Add SideNavItem for `/answer` under Principal in `app-shell.tsx` with `isSelected` via pathname; verify nav highlights on `/answer` and shell still wraps the page

## 4. Integration check

- [x] 4.1 End-to-end: backend up + frontend `npm run dev` → ask a Metropol question → see answer + citations (or clear 503 if no key); verify CORS to `:3000`
- [x] 4.2 Run `graphify update .` after frontend code lands and verify the graph includes the new answer page / client nodes

## Workflow follow-up

- Archive the change after review (`/opsx-archive`) when E1 is accepted.
- Next product slice: `add-agentic-chat-ui` (E2) — not in this change.
