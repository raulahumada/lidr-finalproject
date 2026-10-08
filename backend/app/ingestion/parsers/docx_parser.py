from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from docx import Document


class DocxParser:
    supported_formats: ClassVar[set[str]] = {"docx"}

    def parse(self, path: Path) -> str:
        document = Document(str(path))
        parts = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
        return "\n\n".join(parts)
