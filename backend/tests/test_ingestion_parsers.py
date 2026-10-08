from __future__ import annotations

from pathlib import Path

from app.generation.rag.chunking import chunk_document
from app.ingestion.loaders import iter_corpus_files
from app.ingestion.parsers.md import MdParser
from app.ingestion.parsers.registry import default_registry
from app.ingestion.parsers.txt import TxtParser


def test_txt_and_md_parsers(tmp_path: Path) -> None:
    txt = tmp_path / "a.txt"
    md = tmp_path / "b.md"
    txt.write_text("hola cobranzas", encoding="utf-8")
    md.write_text("# Ventas\n\nTenela", encoding="utf-8")
    assert "cobranzas" in TxtParser().parse(txt)
    assert "Tenela" in MdParser().parse(md)


def test_registry_has_expected_formats() -> None:
    registry = default_registry()
    assert registry.has("pdf")
    assert registry.has("docx")
    assert registry.has("txt")
    assert not registry.has("xlsx")


def test_walker_skips_unknown_extensions(tmp_path: Path) -> None:
    (tmp_path / "keep.txt").write_text("ok", encoding="utf-8")
    (tmp_path / "skip.xlsx").write_text("nope", encoding="utf-8")
    (tmp_path / "skip.mp4").write_bytes(b"\x00\x00")
    keep = []
    skip = []
    for item, path in iter_corpus_files(tmp_path, allowlist={"txt", "md"}):
        if item is None:
            skip.append(path.name)
        else:
            keep.append(item.relative_path)
    assert keep == ["keep.txt"]
    assert set(skip) == {"skip.xlsx", "skip.mp4"}


def test_chunker_splits_long_text() -> None:
    text = "\n\n".join(
        f"Parrafo {i} sobre Metropol Fintech omnicanal cobranzas ventas. " * 10
        for i in range(30)
    )
    chunks = chunk_document(text, extension="txt")
    assert len(chunks) > 1
    assert all(c.content.strip() for c in chunks)
