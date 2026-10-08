"""Knowledge CAG: curated preloadable Metropol context (peer lidr-master pattern).

Measured with tiktoken; over the ceiling → fail loud (never silent truncate).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import tiktoken

_ENCODING = "cl100k_base"
_DEFAULT_PACK = (
    Path(__file__).resolve().parents[2]
    / "foundation"
    / "prompts"
    / "answer"
    / "knowledge"
    / "metropol_v1.md"
)


class ContextTooLargeError(RuntimeError):
    """Rendered knowledge pack exceeds the configured token ceiling."""


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding(_ENCODING)
    return len(enc.encode(text))


def load_knowledge_pack(
    *,
    path: Path | None = None,
    max_tokens: int,
) -> tuple[str, int]:
    """Return (pack_text, token_count). Raises ContextTooLargeError if over ceiling."""
    pack_path = path or _DEFAULT_PACK
    text = pack_path.read_text(encoding="utf-8").strip()
    if "## Qué es este pack" not in text and "## What" not in text:
        # Soft check: prefer an explicit limits section; still require non-empty.
        if "NO" not in text and "no es" not in text.lower():
            raise ValueError(f"Knowledge pack missing limits section: {pack_path}")
    tokens = count_tokens(text)
    if tokens > max_tokens:
        raise ContextTooLargeError(
            f"knowledge pack is {tokens} tokens, {tokens - max_tokens} over the "
            f"{max_tokens} ceiling. Refusing to truncate."
        )
    return text, tokens


@lru_cache
def get_default_knowledge_pack(max_tokens: int) -> str:
    text, _ = load_knowledge_pack(max_tokens=max_tokens)
    return text
