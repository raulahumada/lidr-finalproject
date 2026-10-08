"""Parser protocol: format string → plain text."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Protocol, runtime_checkable


@runtime_checkable
class Parser(Protocol):
    supported_formats: ClassVar[set[str]]

    def parse(self, path: Path) -> str:  # pragma: no cover - protocol stub
        ...
