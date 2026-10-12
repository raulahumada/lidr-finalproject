# Design

## Context

Answer pipeline (Graphify hub `AnswerService` → `render_answer_prompts`) uses `answer/v1` with loosely formatted chunks. Course grounded generation wraps evidence in self-describing blocks and budgets tokens; peer Q&A prompts emphasize partial answers and prose synthesis. Metropol keeps JSON API (`answer` + citations).

## Goals / Non-Goals

**Goals:**
- v2 prompts + budgeted, citable context blocks.
- Citation validation against sent evidence.
- Default to v2 without deleting v1.

**Non-Goals:**
- Agents / LangGraph / conversation memory.
- Full Instructor citation retry loop.
- Changing retrieve/embed models.

## Decisions

1. **New version `answer/v2/`** — never edit v1 in place; `prompt_version` already keys exact/semantic caches.
2. **Markdown numbered blocks** with visible `id=<chunk_id>` and `source_path` — course citability, peer readability (not XML).
3. **One renderer** used for both token counting and prompt text (`fit_to_budget` then `build_context`).
4. **Keep JSON output** from the model (`answer` + `citation_indices` mapping to block order or chunk ids); filter unknowns.
5. **Default budget** ~3500 tokens for retrieve context (setting `answer_context_max_tokens`); knowledge pack separate (existing ceiling).
6. **Partial answer rule** in system: answer what evidence supports; only then say what is missing.

### Layer map

| Piece | Layer |
|-------|--------|
| `answer/v2/*.j2`, loader | `foundation/prompts` |
| `context_blocks.py` (render + budget) | `generation/rag` |
| validate citations + call LLM | `domain/answer_service` |
| settings | `config` |

## Risks / Trade-offs

- Softening + better blocks may still mix ventas/cobranzas if retrieve ranks poorly — prompt cannot fix ranking alone.
- Markdown vs XML: slightly less machine-strict than course; mitigated by id validation.
- After apply: run `graphify update .` to refresh hubs.
