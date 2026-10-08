# Design

## Context

Backend already has pgvector chunks, ingest, recursive/md chunking, and `POST /search`. Course `session_16` stacks Response CAG (exact + semantic Redis) before LLM in a domain conductor; peer `lidr-master` implements Knowledge CAG as a token-measured preload (`process_map/cag.py`). Host is macOS/bash; Compose already runs Postgres.

## Goals / Non-Goals

**Goals:**
- `POST /api/v1/answer` with grounded text + citations + cache provenance.
- Knowledge pack in system prompt (measured, hard ceiling).
- Response caches exact → semantic before RAG+LLM; store after success.
- Jinja system/user templates; thin LLM wrapper; layers respect no cross-imports between `generation` siblings.

**Non-Goals:**
- Agents / LangGraph / frontend chat.
- Full course guardrails / Instructor structured output suite.
- VisualTIME process-map graph; Metropol pack is curated Markdown v1.
- Silent truncation of knowledge pack.

## Decisions

1. **Conductor in `domain/answer_service.py`** — only place that wires `cag` + `rag` + prompts + llm (course rule).
2. **`generation/cag/` = response caches only** — Knowledge preload is `generation/rag/knowledge_pack.py` (or `foundation/prompts/answer/knowledge/`) so Redis CAG is not confused with paper-style CAG.
3. **Redis Stack in Compose** — required for semantic index (RediSearch); exact cache uses same Redis URL; Redis failures → miss, not 500.
4. **Semantic `log_only=true` by default** — calibrate threshold without serving hits until tuned.
5. **No-evidence without LLM** — empty retrieve → fixed message, `citations=[]`, do not cache as a “successful” answer (or cache only if we mark `no_evidence=true` and skip — prefer **do not store**).
6. **JSON-ish LLM output** — ask model for `answer` + citation indices into retrieved list; citations filled from retrieve metadata.
7. **Prompt version in cache keys** — changing Jinja/`prompt_version` invalidates caches.

### Layer map

| Module | Layer |
|--------|--------|
| `foundation/prompts`, `foundation/llm` | foundation |
| `generation/cag/*` | generation (response CAG) |
| `generation/rag/knowledge_pack.py`, retriever | generation (rag sibling) |
| `domain/answer_service.py` | conductor |
| `api/routes/answer.py` | api (thin) |

## Risks / Trade-offs

- Knowledge pack stale vs corpus → keep pack short (policy/limits), rely on RAG for facts.
- Semantic false positives → `log_only` until eval.
- Extra Compose service → document in AGENTS; answer still works if Redis down (always miss).
- Minimal LLM wrapper may need richer validation later.
