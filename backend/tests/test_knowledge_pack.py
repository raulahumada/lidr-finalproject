from pathlib import Path

import pytest

from app.generation.rag.knowledge_pack import (
    ContextTooLargeError,
    count_tokens,
    load_knowledge_pack,
)


def test_default_pack_loads_under_ceiling() -> None:
    text, tokens = load_knowledge_pack(max_tokens=4096)
    assert "Metropol" in text
    assert "NO" in text or "no" in text.lower()
    assert tokens == count_tokens(text)
    assert tokens > 0


def test_pack_over_ceiling_fails_loud(tmp_path: Path) -> None:
    fat = tmp_path / "fat.md"
    fat.write_text("## Qué es este pack y qué NO es\n\n" + ("palabra " * 5000), encoding="utf-8")
    with pytest.raises(ContextTooLargeError):
        load_knowledge_pack(path=fat, max_tokens=10)
