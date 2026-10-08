from __future__ import annotations

from app.ingestion.parsers.docx_parser import DocxParser
from app.ingestion.parsers.md import MdParser
from app.ingestion.parsers.pdf import PdfParser
from app.ingestion.parsers.protocol import Parser
from app.ingestion.parsers.txt import TxtParser


class ParserRegistry:
    def __init__(self) -> None:
        self._by_format: dict[str, Parser] = {}

    def register(self, parser: Parser) -> None:
        for fmt in parser.supported_formats:
            key = fmt.lower().lstrip(".")
            if key in self._by_format:
                raise ValueError(f"Format {key!r} already registered")
            self._by_format[key] = parser

    def get(self, fmt: str) -> Parser:
        key = fmt.lower().lstrip(".")
        try:
            return self._by_format[key]
        except KeyError as exc:
            raise KeyError(f"No parser registered for format {key!r}") from exc

    def has(self, fmt: str) -> bool:
        return fmt.lower().lstrip(".") in self._by_format

    def formats(self) -> set[str]:
        return set(self._by_format)


def default_registry() -> ParserRegistry:
    registry = ParserRegistry()
    registry.register(TxtParser())
    registry.register(MdParser())
    registry.register(PdfParser())
    registry.register(DocxParser())
    return registry
