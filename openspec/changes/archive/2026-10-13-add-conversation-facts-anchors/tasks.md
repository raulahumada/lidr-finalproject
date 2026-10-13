# Tasks

## 1. Backend — models + facts + anchors

- [x] 1.1 Add `models.py`, `facts.py`, `anchors.py` (Metropol-shaped, no LLM extract)
- [x] 1.2 Persist/merge facts+anchors on session (`store` + Alembic only if needed)
- [x] 1.3 Wire into `resolve` / runner hydrate / `render_memory` (+ light retrieve bias)
- [x] 1.4 Unit tests: facts merge, anchor detect, no empty-retrieve pin

## 2. Docs + verify

- [x] 2.1 Update root `AGENTS.md` memory model (window + facts + anchors)
- [x] 2.2 `cd backend && .venv/bin/python -m pytest -q` (conversation + related)
- [x] 2.3 `graphify update .`
