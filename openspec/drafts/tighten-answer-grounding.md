# Draft: tighten-answer-grounding

## Surface
- Primary: **backend** (prompts + composer/gate); docs
- Paths: `grounded_composer`, prompts `answer/v2`, posiblemente `escalation_gate` / confidence; tests de prompts; `AGENTS.md`
- Course: citación verificable + abstención (Sesión 11)
- Peer: revise-answer-synthesis-prompt / no inventar endpoints

## Intent
Cuando la evidencia es fina, el modelo aún arma procedimientos largos (handoff “completo”) y cierra con “no hay info suficiente”. Apretar **abstención / longitud / no-procedimiento** para alinear respuesta con guardrails Metropol y con lo que el eval ya mide.

## Graphify notes
- Hubs: `grounded_composer`, `source_guard`, `review_reasons` / `no_evidence`, knowledge pack Metropol
- No tocar UI salvo copy de mensajes de review (non-goal)

## Non-goals
- RAGAS
- Cambiar retrieve/chunking
- Facts/anchors (otro draft)
- Reescribir todo el prompt v2 desde cero

## Draft requirements
- Si `no_evidence` o hits vacíos: respuesta **corta** de abstención (sin pasos operativos numerados inventados); preferir escalate
- Si hay hits pero cobertura parcial: exigir que el modelo **no invente** pasos no soportados; template/instrucción explícita en system/user v2
- Opcional: bajar confidence o añadir review_reason cuando la respuesta es larga y `citations` < N (heurística simple)
- Tests de prompt/fixture (estilo `test_answer_prompts_v2`) + caso eval golden existente de out-of-corpus sigue pasando
- Docs: nota en `AGENTS.md` / prompts version note (bump `ANSWER_PROMPT_VERSION` solo si hace falta invalidar CAG — **preferir v2 iter + flush Redis** documentado)

## Approach sketch
1. Ajustar `system.j2` / user block Metropol: reglas de abstención + “no listes procedimiento si el excerpt no lo detalla”
2. `grounded_composer`: si no_evidence, short-circuit a template fijo (sin LLM) o prompt mínimo
3. Tests + re-correr eval smoke `--case out-of-corpus-*`

## Practices check (backend | both only)
- Aligned: cambios en prompts + domain agent; settings threshold si aplica
- Deviations: none expected
- Risks if ignored: over-abstain en preguntas válidas → calibrar con golden set

## Impact
- backend: prompts + composer/gate + tests
- frontend: none

## Open questions
- ¿Short-circuit sin LLM en no_evidence? → **Default: sí** (barato, determinista)
- ¿Bump prompt version a v3? → **Default: no**; iterar v2 + flush cache

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change 
- Promoted to openspec change `tighten-answer-grounding`
