from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pypdf import PdfReader


class PdfParser:
    supported_formats: ClassVar[set[str]] = {"pdf"}

    def parse(self, path: Path) -> str:
        reader = PdfReader(str(path))
        parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            if text.strip():
                parts.append(text)
        return "\n\n".join(parts)
