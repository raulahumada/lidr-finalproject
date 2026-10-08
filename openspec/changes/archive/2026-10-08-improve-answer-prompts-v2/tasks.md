# Tasks

## 1. Context blocks + settings

- [x] 1.1 Add `generation/rag/context_blocks.py` (render numbered blocks with `chunk_id` + `source_path`; `fit_to_budget` dropping whole chunks)
- [x] 1.2 Add `answer_context_max_tokens` setting (default ~3500); default `answer_prompt_version` to `v2` in settings + `.env.example`

## 2. Prompts v2

- [x] 2.1 Add `answer/v2/system.j2` + `user.j2` (partial-answer rules, knowledge pack subordinated, cite only sent block ids)
- [x] 2.2 Extend loader to render v2 with `context` string (keep v1 working)

## 3. Conductor wiring

- [x] 3.1 Update `AnswerService` to budget → build context → render v2 → validate citation ids/indices against sent hits
- [x] 3.2 Wire settings in `dependencies`; document version bump / Redis flush in `AGENTS.md`

## 4. Tests

- [x] 4.1 Unit tests: block provenance, budget drops whole chunk, fabricated citation filtered, v2 system contains partial-answer policy
- [x] 4.2 Existing answer tests still green; `graphify update .` after apply
