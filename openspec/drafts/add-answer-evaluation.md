# Draft: add-answer-evaluation

## Surface
- Primary: **backend**
- Paths in this repo: `backend/eval/` (harness + golden set + reports), `backend/AGENTS` notes via root `AGENTS.md`; tests ligeros del scoring offline si aplica
- Course reference (`session_16` / `ai-service`): `eval/run_eval.py` + `golden_set.json` (harness contra servicio desplegado, exit ≠ CI gate); `evals/` RAGAS = follow-up, no v1
- Patterns borrowed (not copied): golden JSON + CLI HTTP contra API local; checks deterministas sobre citas/flags; no gastar tokens en CI

## Intent
Tener un **harness de evaluación Metropol** runnable a mano: set chico de preguntas → `POST /answer/agentic` (sync) → score de groundedness/citas/abstención. Cierra el gap “¿la respuesta inventa handoff?” con evidencia medible, alineado al entregable de evaluación del curso sin montar RAGAS todavía.

## Graphify notes
- Queried: `answer evaluation groundedness citations agentic eval`
- Hubs: `AgenticAnswerRunner`, `source_guard`, `Citation`, `answer_agentic`, `review_reasons` / `citations_valid`
- Edges: harness debe consumir el contrato HTTP ya existente (no nuevo island de scoring en el hot path)
- Gaps: no hay módulo `eval` en este monorepo aún → carpeta nueva `backend/eval/` (como el peer), fuera del hot path

## Non-goals
- RAGAS / LLM-as-judge en v1 (caro, no determinista)
- Gatear CI/pytest con llamadas reales a OpenAI
- UI de dashboard de evals
- Cambiar prompts/composer (eso sería un change aparte si el harness falla mucho)
- Auth / deploy cloud

## Draft requirements
- Golden set JSON (≈8–12 casos) con: `id`, `question`, `domain` opcional, expectativas:
  - `expect_citations` (bool)
  - `expect_no_evidence` o `expect_pause` (bool)
  - `must_mention` / `must_not_mention` (listas opcionales de substrings, case-insensitive)
  - `notes` (humano)
- CLI: `python -m eval.run_eval --base-url http://localhost:8000 [--limit N] [--case id]`
  - Llama sync agentic (`POST /api/v1/answer/agentic`)
  - Auto-approve resume si status `awaiting_human_review` (opcional flag `--auto-approve`) para poder puntuar el borrador
- Scoring por caso (pass/fail + reasons):
  - Si `expect_citations`: al menos 1 citation y `citations_valid` no es False
  - Cada `citation.chunk_id` coherente con payload (ya validado por source_guard; re-check presence)
  - `must_mention` / `must_not_mention` sobre `answer`
  - `expect_pause` / `expect_no_evidence` alineado a flags/status
- Report JSON (+ print resumen) en `backend/eval/reports/` (gitignore reports o dejar solo `.gitkeep`)
- Exit code 0 solo si todos los casos ejecutados pasan
- Documentar en root `AGENTS.md` cómo correrlo (API up + OPENAI_API_KEY + corpus ingerido)
- Test unitario offline del scorer con fixtures (sin red)

## Approach sketch
1. `backend/eval/golden_set.json` — casos Metropol (handoff cobranzas, Tenela, omnicanal, pregunta fuera de corpus, etc.).
2. `backend/eval/scoring.py` — funciones puras caso→resultado.
3. `backend/eval/run_eval.py` — httpx client, argparse, report.
4. `backend/tests/test_eval_scoring.py` — scoring puro.
5. `.gitignore` `backend/eval/reports/*.json` excepto `.gitkeep`.
6. Docs + graphify update post-apply.

## Practices check (backend | both only)
- Aligned: harness fuera de `app/api` (no ensucia routers); scoring puro testeable; settings/env vía URL CLI; no secretos en golden set
- Deviations: carpeta `backend/eval/` hermana de `app/` (como el peer), no bajo `app/generation` — **consciente**: eval no es hot path ni capa de generación
- Risks if ignored: meter eval en pytest CI con LLM → flaky + costo; o acoplar scoring al runner y no poder correr contra API real

## Impact
- backend: `eval/` + test scorer + AGENTS.md
- frontend: none

## Open questions
- ¿Path sync agentic o live start+poll? → **Default: sync** `/answer/agentic` (más simple para harness).
- ¿Incluir path sync `/answer` (CAG) también? → **No en v1**; solo agentic.
- ¿Umbral de similitud semántica? → **No en v1**; solo substrings + flags de citas.

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `add-answer-evaluation`
- Synced to main specs + archived `2026-10-13-add-answer-evaluation`
