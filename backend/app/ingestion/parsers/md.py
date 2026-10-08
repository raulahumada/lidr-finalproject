from __future__ import annotations

from pathlib import Path
from typing import ClassVar


class MdParser:
    supported_formats: ClassVar[set[str]] = {"md"}

    def parse(self, path: Path) -> str:
        return path.read_text(encoding="utf-8", errors="replace")
