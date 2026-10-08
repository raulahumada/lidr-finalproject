"""Filesystem walker over CORPUS_ROOT."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusFile:
    absolute_path: Path
    relative_path: str
    extension: str


def iter_corpus_files(
    root: Path,
    *,
    allowlist: set[str],
) -> Iterator[tuple[CorpusFile | None, Path]]:
    """Yield ``(CorpusFile, path)`` for allowlisted files, or ``(None, path)`` for skips.

    The second element is always the absolute path seen (for summary counting).
    """
    allow = {ext.lower().lstrip(".") for ext in allowlist}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith("."):
            continue
        ext = path.suffix.lower().lstrip(".")
        if not ext or ext not in allow:
            yield None, path
            continue
        relative = path.relative_to(root).as_posix()
        yield CorpusFile(absolute_path=path, relative_path=relative, extension=ext), path
