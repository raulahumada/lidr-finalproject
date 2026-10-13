# Draft: add-multiturn-eval

## Surface
- Primary: **backend**
- Paths: `backend/eval/` (golden multiturn + runner/scoring extend); tests offline del resolver scoring; docs `AGENTS.md`
- Course: `evals/` RAGAS — no v1
- Peer Cristian: `add-multiturn-conversation-eval` — golden **secuencias**, mide **falso negativo** del resolver + calidad de rewrite; runner por el **grafo** (no solo `generate_answer`)

## Intent
Extender el harness de `add-answer-evaluation` a **diálogos 2+ turnos** con `session_id`, midiendo si el follow-up se reescribe bien y si la respuesta final sigue grounded — el hueco que Cristian midió después de conversation-memory.

## Graphify notes
- Queried: `eval scoring golden set agentic`
- Hubs: `eval/run_eval.py`, `score_case`, `resolve`, agentic session APIs
- Extender eval package existente; no isla nueva

## Non-goals
- RAGAS / LLM-as-judge
- Gatear CI con corridas live
- Cambiar el resolver (si el eval falla, change aparte de producto)
- Frontend

## Draft requirements
- Golden multiturn JSON: cada caso = `id`, `turns: [{question, …}]`, expectativas por turno:
  - `expect_resolved_contains` / `expect_resolved_equals` (opcional)
  - `expect_rewrite` bool (¿debe diferir de la pregunta escrita?)
  - flags actuales: citations / must_mention / no_evidence
- Runner: crear session → por cada turn `POST /answer/agentic` con `session_id` → score → opcional `--auto-approve`
- Medir **falso negativo**: turn con referente claro + `expect_rewrite=true` y `resolved_question` ausente/igual → fail
- Report JSON con resultados por turn
- Offline tests del scorer multiturn (fixtures, sin red)
- CLI: `python -m eval.run_eval --multiturn` o `python -m eval.run_multiturn` (preferir subcomando/flag en el harness existente)
- Docs en `AGENTS.md`

## Approach sketch
1. `eval/golden_multiturn.json` (6–10 secuencias Metropol: “¿handoff cobranzas?” → “¿y con Tenela?”)
2. Extender `scoring.py` con `score_multiturn_turn(...)` usando `resolved_question` del payload si se expone; si no está en response hoy → **exponer en agentic response** (pequeño contrato) o leer solo rewrite vía campo ya presente
3. Runner loop session + turns
4. Tests + docs

## Practices check (backend | both only)
- Aligned: eval fuera de `app/`; scorer puro; live opt-in
- Deviations: si hay que añadir `resolved_question` al DTO agentic → cambio de contrato mínimo documentado (surface still backend)
- Risks if ignored: solo medir 1-turn → memoria “verde” sin saber si el follow-up falla

## Impact
- backend: `eval/*`, posiblemente `schemas/agentic_answer.py` + runner map de `resolved_question`, tests, docs
- frontend: none

## Open questions
- ¿Exponer `resolved_question` en `AgenticAnswerResponse`? → **Default: sí** (ya existe en state; UI/debug + eval)
- ¿Flag `--multiturn` vs módulo aparte? → **Default: `python -m eval.run_multiturn`** para no ensuciar el CLI 1-turn

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change 
- Promoted to openspec change `add-multiturn-eval`
