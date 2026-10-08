"""Simple paragraph / fixed-size chunking for ingest."""

from __future__ import annotations

import re

DEFAULT_MAX_CHARS = 800
DEFAULT_OVERLAP = 100


def chunk_text(
    text: str,
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap: int = DEFAULT_OVERLAP,
) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", cleaned) if p.strip()]
    if not paragraphs:
        paragraphs = [cleaned]

    chunks: list[str] = []
    buffer = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if buffer:
                chunks.append(buffer)
                buffer = ""
            chunks.extend(_split_long(paragraph, max_chars=max_chars, overlap=overlap))
            continue
        candidate = f"{buffer}\n\n{paragraph}".strip() if buffer else paragraph
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
            buffer = paragraph
    if buffer:
        chunks.append(buffer)
    return [c for c in chunks if c.strip()]


def _split_long(text: str, *, max_chars: int, overlap: int) -> list[str]:
    if max_chars <= 0:
        return [text]
    step = max(1, max_chars - max(0, overlap))
    parts: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        parts.append(text[start:end].strip())
        if end >= len(text):
            break
        start += step
    return [p for p in parts if p]
