# Tasks

## 1. Backend — contract + multiturn eval

- [x] 1.1 Expose `resolved_question` on `AgenticAnswerResponse` (+ progress if trivial) via runner map
- [x] 1.2 Add `golden_multiturn.json` + `score_multiturn_turn` in `scoring.py` + unit tests
- [x] 1.3 Implement `eval/run_multiturn.py` (session loop, `--auto-approve`, reports)
- [x] 1.4 Document in root `AGENTS.md`

## 2. Verify

- [x] 2.1 `pytest -q tests/test_eval_scoring.py` (+ new multiturn scoring tests)
- [x] 2.2 `graphify update .`
