# Draft: upgrade-rag-chunking

## Surface
- Primary: **backend**
- Paths in this repo: `backend/app/generation/rag/chunking.py` (o paquete `chunking/`), `backend/app/ingestion/orchestrator.py`, tests, `AGENTS.md`, posiblemente `requirements.txt` (`langchain-text-splitters` / `tiktoken`)
- Course reference (branch/path): `session_16` → `.reference/ai-engineering/ai-service/app/generation/rag/chunking/strategies/recursive.py` (+ structural / markdown patterns del artículo sesión 7)
- Patterns borrowed (not copied):
  - **Recursive** default: 512 tokens, overlap ~80 (10–20%), separadores `["\n\n", "\n", ". ", " ", ""]`
  - Estrategia por tipo de documento cuando hay estructura (md headers; heurística de secciones en docx/pdf)
  - Medir sobre corpus propio antes de semantic/LLM chunking
  - Normalización ligera de whitespace post-parse (colapsar newlines excesivos; opcional unir líneas partidas de PDF)

## Intent
Mejorar la calidad de retrieval del corpus Metropol reemplazando el chunker párrafo/fixed-size actual por el **baseline del curso** (recursive) y chunking **estructural** donde el formato lo permita, luego re-ingerir con `--force`.

## Non-goals
- Semantic / LLM / propositional / late / agentic / query-dependent chunking
- Contextual Retrieval (Anthropic) — follow-up si recursive no alcanza
- Parent-child / hierarchical retrieval architecture
- Cambiar modelo de embeddings o añadir HNSW
- `/answer` o UI
- Re-parse con otra librería PDF (sigue pypdf / python-docx)

## Draft requirements
- API de chunking tipada, p. ej. `chunk_document(text, *, document_type|extension) -> list[ChunkPiece]` con metadata opcional (`section`, `strategy`).
- Default strategy **recursive** (~512 tokens / ~10–20% overlap); implementación vía `langchain-text-splitters` + tiktoken **o** equivalente mínimo sin LangChain si se prefiere menos deps — **propuesta: usar `langchain-text-splitters` como el curso** para no reinventar.
- Strategies por extensión:
  - `md`: split por headers Markdown (`#` / `##` / `###`) y recursive dentro de secciones grandes
  - `txt` / `pdf` / `docx`: recursive sobre texto normalizado; si se detectan headings (líneas cortas / numeración), guardar `section` en metadata del chunk cuando sea barato
- Normalización pre-chunk: strip; colapsar ≥3 newlines a 2; opcional heurística PDF line-join.
- Orchestrator usa el nuevo chunker; `chunk_type` / metadata reflejan `strategy`.
- Tests unitarios: recursive no corta a mitad de palabra en prosa típica; md respeta headers; texto vacío → [].
- Docs: cómo re-ingerir (`python -m app.ingestion.run_ingest --force`) tras el cambio.
- Tras apply: re-ingest Metropol y smoke `/search` (comparar a ojo 5–10 queries).

## Approach sketch
1. Refactor `generation/rag/chunking.py` → módulo con `normalize_text` + `RecursiveChunker` + `MarkdownChunker`.
2. Wire en `ingestion/orchestrator.py` pasando extensión del archivo.
3. Deps: `langchain-text-splitters`, `tiktoken` (si se usa from_tiktoken_encoder).
4. Re-ingest `--force` en verificación.
5. Capability OpenSpec: modificar `corpus-ingest` (requisito de chunking) **o** nueva `rag-chunking` — **propuesta: `rag-chunking`** (comportamiento durable del splitter, independiente del walk de archivos).

## Practices check (backend | both only)
- Aligned:
  - Chunking en `generation/rag`; ingestion solo orquesta
  - Settings existentes; sin secretos nuevos
  - Tests unitarios del splitter
- Deviations (+ why):
  - Añadir LangChain text-splitters (solo el splitter, no el framework RAG completo). **Por qué:** mismo default medido del curso; alternativa stdlib es más código y drift.
  - Sin eval formal golden-set en este change. **Por qué:** smoke + re-ingest basta para el slice; evals = change aparte.
- Risks if ignored:
  - Seguir con fixed-size/paragraph → retrieval difuso (artículo sesión 7)
  - Saltar a semantic sin medir → coste sin evidencia

## Impact
- backend: chunking module, orchestrator, deps, tests, docs
- frontend: ninguno
- ops: re-ingest local obligatorio para ver el efecto

## Open questions
- ¿LangChain text-splitters o recursive casero? **Propuesta: langchain-text-splitters** (curso).
- ¿Re-ingest automático en apply o solo documentado? **Propuesta: correr `--force` en verificación del apply** (tiene API key + CORPUS_ROOT en la máquina del user).

## Status
- [x] User approved — ready for OpenSpec propose
- Promoted to openspec change `upgrade-rag-chunking`
- Implemented, specs synced, archived as `2026-10-08-upgrade-rag-chunking`
