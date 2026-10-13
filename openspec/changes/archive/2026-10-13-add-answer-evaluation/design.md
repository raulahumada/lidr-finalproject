# Design

## Context

See proposal.md — Why. Graphify hubs for the evaluated path: `AgenticAnswerRunner`, `source_guard`, citation fields on agentic payloads. Course peer: `ai-service/eval/run_eval.py` (HTTP harness + golden JSON, deliberate runs, not ordinary CI).

## Goals / Non-Goals

**Goals:**
- Deterministic pass/fail scoring over agentic JSON responses
- CLI against a running local API
- Offline unit tests for scoring only

**Non-Goals:**
- RAGAS / LLM-as-judge
- Changing composer prompts or retrieval
- Dashboard UI
- Gating merge CI on live OpenAI calls

## Decisions

### 1. Layout: `backend/eval/` sibling of `app/`

**Choice:** Mirror course `eval/` at `backend/eval/` (`golden_set.json`, `scoring.py`, `run_eval.py`, `reports/`).

**Why:** Not part of the FastAPI hot path; avoids layering eval into `generation/` or `domain/`.

**Alt:** `backend/app/evaluation/` — rejected; peers and scripts live outside the service package.

### 2. Target endpoint: sync agentic

**Choice:** `POST {base}/api/v1/answer/agentic` with optional `domain`.

**Why:** One request returns terminal or pause payload; simpler than start/progress poll.

**Alt:** Live progress poll — deferred.

### 3. Pause handling

**Choice:** Default score the pause payload (status `awaiting_human_review`, draft answer/citations if present). Flag `--auto-approve` posts resume `approve` then scores the final body.

**Why:** Many Metropol cases may trip the gate; harness must still produce a signal.

### 4. Scoring rules (v1)

**Choice:** Pure functions:
- `expect_citations` → ≥1 citation and `citations_valid is not False`
- `expect_no_evidence` → `no_evidence is True` (and/or empty citations as documented in golden notes)
- `expect_pause` → status is `awaiting_human_review` (before auto-approve)
- `must_mention` / `must_not_mention` → case-insensitive substring checks on `answer` (empty answer fails `must_mention`)

**Why:** Cheap, stable, aligned with `source_guard` flags already on the wire.

**Alt:** RAGAS faithfulness — follow-up change.

### 5. Module import path

**Choice:** Run as `python -m eval.run_eval` from `backend/` with `eval` as a top-level package (add `backend/eval/__init__.py`). Ensure `httpx` is already a dependency or add if missing.

**Why:** Matches course mental model; no packaging into `app`.

## Risks / Trade-offs

- [Golden expectations drift vs real corpus] → Keep cases loose (`must_mention` soft); refresh notes when ingest changes
- [Paid / slow runs] → Document `--limit` / `--case`; never wire into default pytest
- [Pause + auto-approve doubles latency] → Opt-in flag only

## Open Questions

None — draft defaults accepted.
