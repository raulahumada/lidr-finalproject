from app.generation.rag.context_blocks import (
    build_context,
    fit_to_budget,
    render_hit_block,
)
from app.schemas.search import SearchHit


def _hit(chunk_id: int, content: str, path: str = "a.md") -> SearchHit:
    return SearchHit(
        chunk_id=chunk_id,
        document_id=1,
        chunk_type="recursive",
        content=content,
        score=0.9,
        distance=0.1,
        source_path=path,
        document_type="md",
        metadata={"strategy": "recursive", "section": "Intro"},
    )


def test_render_includes_provenance() -> None:
    text = render_hit_block(1, _hit(42, "hola mundo"))
    assert "[id=42]" in text
    assert "source_path: a.md" in text
    assert "section: Intro" in text
    assert "hola mundo" in text


def test_fit_to_budget_drops_whole_chunk() -> None:
    hits = [
        _hit(1, "alpha " * 50),
        _hit(2, "beta " * 50),
        _hit(3, "gamma " * 50),
    ]
    # Tiny budget: only first block should fit after the first is kept.
    first_block = render_hit_block(1, hits[0])
    from app.generation.rag.context_blocks import count_tokens

    budget = count_tokens(first_block) + 5
    kept = fit_to_budget(hits, max_tokens=budget)
    assert len(kept) == 1
    assert kept[0].hit.chunk_id == 1
    assert "alpha" in build_context(kept)
    assert "gamma" not in build_context(kept)
