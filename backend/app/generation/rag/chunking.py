"""Normalize + recursive / Markdown chunking for RAG ingest.

Aligned with course session_16 RecursiveChunker defaults (512 tokens / 80 overlap).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

CHUNK_SIZE_TOKENS = 512
OVERLAP_TOKENS = 80
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

_RECURSIVE = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    chunk_size=CHUNK_SIZE_TOKENS,
    chunk_overlap=OVERLAP_TOKENS,
    separators=SEPARATORS,
)

_MD_HEADERS = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ],
    strip_headers=False,
)


@dataclass(frozen=True)
class ChunkPiece:
    content: str
    strategy: str
    section: str | None = None


def normalize_text(text: str, *, extension: str = "") -> str:
    """Light cleanup before splitting (ingest-time, not answer-time)."""
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return ""

    ext = extension.lower().lstrip(".")
    if ext == "pdf":
        cleaned = _join_pdf_line_breaks(cleaned)

    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _join_pdf_line_breaks(text: str) -> str:
    """Join single newlines that look like mid-sentence wraps (conservative)."""
    lines = text.split("\n")
    if len(lines) <= 1:
        return text

    out: list[str] = [lines[0]]
    for line in lines[1:]:
        prev = out[-1]
        if (
            prev
            and line
            and not prev.endswith((".", "!", "?", ":", ";"))
            and not line.startswith(("#", "-", "*", "•", "○", "●"))
            and (line[0].islower() or line[0].isdigit())
            and not prev.endswith("\n")
        ):
            out[-1] = f"{prev.rstrip()} {line.lstrip()}"
        else:
            out.append(line)
    return "\n".join(out)


def chunk_document(text: str, *, extension: str) -> list[ChunkPiece]:
    """Split extracted text into embeddable pieces for the given file extension."""
    ext = extension.lower().lstrip(".")
    normalized = normalize_text(text, extension=ext)
    if not normalized:
        return []

    if ext == "md":
        return _chunk_markdown(normalized)
    return _chunk_recursive(normalized, section=None)


def _chunk_recursive(text: str, *, section: str | None) -> list[ChunkPiece]:
    pieces = _RECURSIVE.split_text(text)
    return [
        ChunkPiece(content=piece.strip(), strategy="recursive", section=section)
        for piece in pieces
        if piece.strip()
    ]


def _chunk_markdown(text: str) -> list[ChunkPiece]:
    try:
        sections = _MD_HEADERS.split_text(text)
    except Exception:  # noqa: BLE001 — fall back if header split fails
        return _chunk_recursive(text, section=None)

    if not sections:
        return _chunk_recursive(text, section=None)

    results: list[ChunkPiece] = []
    for doc in sections:
        body = (doc.page_content or "").strip()
        if not body:
            continue
        meta = doc.metadata or {}
        section = meta.get("h3") or meta.get("h2") or meta.get("h1")
        # Oversized sections: recursive inside the section boundary.
        for piece in _RECURSIVE.split_text(body):
            content = piece.strip()
            if content:
                results.append(
                    ChunkPiece(content=content, strategy="markdown", section=section)
                )

    return results or _chunk_recursive(text, section=None)


# Backward-compatible alias for older tests; prefer chunk_document.
def chunk_text(text: str, *, max_chars: int = 800, overlap: int = 100) -> list[str]:
    """Deprecated: delegates to recursive chunk_document (ignores max_chars/overlap)."""
    _ = max_chars, overlap
    return [p.content for p in chunk_document(text, extension="txt")]
