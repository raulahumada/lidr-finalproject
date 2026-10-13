# Tasks

## 1. Backend — eval package

- [x] 1.1 Create `backend/eval/` package (`__init__.py`, `golden_set.json` ~8–12 Metropol cases, `reports/.gitkeep`)
- [x] 1.2 Implement pure `scoring.py` (citations / mentions / pause / no_evidence) + `tests/test_eval_scoring.py`
- [x] 1.3 Implement `run_eval.py` CLI (`--base-url`, `--limit`, `--case`, `--auto-approve`) → JSON report + exit code
- [x] 1.4 Gitignore `backend/eval/reports/*.json` (keep `.gitkeep`)

## 2. Docs + verify

- [x] 2.1 Document harness in root `AGENTS.md` (API up, key, corpus, example command)
- [x] 2.2 `cd backend && .venv/bin/python -m pytest -q tests/test_eval_scoring.py`
- [x] 2.3 `graphify update .`

## Workflow follow-up

- Live smoke (optional, not CI): API up → `python -m eval.run_eval --limit 1`
- Archive after apply when ready
- `/commit-pr` when the user asks
