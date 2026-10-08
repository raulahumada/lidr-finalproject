# Design

## Context

See `proposal.md`. Current `chunk_text` in `generation/rag/chunking.py` is paragraph/fixed-size. Course `RecursiveChunker` uses `RecursiveCharacterTextSplitter.from_tiktoken_encoder` (512 / 80, separators `\n\n` → `\n` → `. ` → ` ` → `""`). Metropol corpus already ingested; must `--force` to refresh vectors.

Layer map: `normalize` + strategies in `generation/rag`; `ingestion/orchestrator` calls `chunk_document(...)`.

## Goals / Non-Goals

**Goals:** recursive default; md headers; light normalize; wire ingest; tests; re-ingest verify.

**Non-Goals:** semantic/LLM chunking, contextual retrieval, changing parsers.

## Decisions

1. **Capability `rag-chunking`** — durable splitter behavior separate from `corpus-ingest` walk.
2. **`langchain-text-splitters` + tiktoken`** — match course; accept small dep surface.
3. **Public API** — `ChunkPiece(content, strategy, section: str | None)` + `chunk_document(text, *, extension: str) -> list[ChunkPiece]`.
4. **Normalize** — shared `normalize_text(text, *, extension)`; for `pdf` also join hyphen/newline mid-sentence heuristically (conservative: join when line break is single `\n` and next line starts lowercase / continuation).
5. **MD path** — `MarkdownHeaderTextSplitter` then recursive on oversized sections.
6. **Persist metadata** — orchestrator writes `strategy` (+ `section` if any) into chunk metadata JSONB; `chunk_type` can stay `paragraph` or become strategy name — **use `chunk_type=strategy`** for clarity.
7. **Apply verification** — run `python -m app.ingestion.run_ingest --force` on developer CORPUS_ROOT.

## Risks / Trade-offs

- **[Risk] Re-ingest cost (OpenAI embeddings)** → Expected; document; operator already has key.
- **[Risk] LangChain dep churn** — pin `>=` floors; only import text_splitters.
- **[Trade-off] Heading heuristics for docx/pdf weak** — md gets full structural; others rely on recursive (honest to article).

## Migration Plan

1. Ship code + deps → unit tests.  
2. `--force` ingest → smoke `/search`.  
3. Rollback: revert code + `--force` again with old chunker if needed (no schema migration).

## Open Questions

None blocking (draft proposals locked).
