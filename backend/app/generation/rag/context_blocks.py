"""Budgeted, citable context blocks for answer prompts (course + peer pattern)."""

from __future__ import annotations

from dataclasses import dataclass

import tiktoken

from app.schemas.search import SearchHit

_ENCODING = "cl100k_base"


@dataclass(frozen=True)
class ContextBlock:
    index: int  # 0-based among kept blocks (citation_indices)
    hit: SearchHit
    text: str


def count_tokens(text: str) -> int:
    return len(tiktoken.get_encoding(_ENCODING).encode(text))


def render_hit_block(display_number: int, hit: SearchHit) -> str:
    """One numbered block; provenance first. Same text for budget and prompt."""
    section = ""
    strategy = ""
    if isinstance(hit.metadata, dict):
        if hit.metadata.get("section"):
            section = f"\nsection: {hit.metadata['section']}"
        if hit.metadata.get("strategy"):
            strategy = f"\nstrategy: {hit.metadata['strategy']}"
    return (
        f"### {display_number}. [id={hit.chunk_id}]\n"
        f"source_path: {hit.source_path}\n"
        f"document_type: {hit.document_type}"
        f"{section}{strategy}\n\n"
        f"{hit.content.strip()}"
    )


def build_context(blocks: list[ContextBlock]) -> str:
    return "\n\n".join(block.text for block in blocks)


def fit_to_budget(
    hits: list[SearchHit],
    *,
    max_tokens: int,
) -> list[ContextBlock]:
    """Keep leading hits whose wrapped blocks fit; drop whole chunks only."""
    kept: list[ContextBlock] = []
    used = 0
    for hit in hits:
        display_number = len(kept) + 1
        text = render_hit_block(display_number, hit)
        cost = count_tokens(text) + (2 if kept else 0)
        if kept and used + cost > max_tokens:
            break
        if not kept and count_tokens(text) > max_tokens:
            # Oversized first chunk: keep intact (never mid-truncate).
            kept.append(ContextBlock(index=0, hit=hit, text=text))
            break
        kept.append(ContextBlock(index=len(kept), hit=hit, text=text))
        used += cost
    return kept
