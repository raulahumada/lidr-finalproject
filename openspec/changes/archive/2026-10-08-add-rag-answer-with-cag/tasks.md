# Tasks

## 1. Infra and settings

- [x] 1.1 Add Redis Stack service to root `docker-compose.yml` + document `REDIS_URL` in `.env.example` / `AGENTS.md`
- [x] 1.2 Extend `backend` settings (redis URL, TTLs, semantic threshold, `log_only`, chat model, prompt version, knowledge max tokens, default k) and add deps (`jinja2`, `redis`, `redisvl`/`numpy` as needed)

## 2. Knowledge CAG + prompts

- [x] 2.1 Add Metropol knowledge Markdown + `knowledge_pack` renderer with tiktoken measure and hard ceiling
- [x] 2.2 Add Jinja loader + `answer/v1/system.j2` + `user.j2`

## 3. Response CAG

- [x] 3.1 Implement `generation/cag/exact.py` (SHA-256 get/set, soft-fail)
- [x] 3.2 Implement `generation/cag/semantic.py` (bucket + similarity, `log_only`)

## 4. Answer pipeline + API

- [x] 4.1 Thin `foundation/llm` chat wrapper (OpenAI)
- [x] 4.2 `domain/answer_service.py` conductor: exact → semantic → retrieve → no-evidence / generate → store
- [x] 4.3 Schemas + `POST /api/v1/answer` route wired in `dependencies` / router

## 5. Verification

- [x] 5.1 Pytest: exact hit, no-evidence, miss+mock LLM, semantic log_only, API 503 without key
- [x] 5.2 Document curl example in `AGENTS.md`; mark draft promoted
