from __future__ import annotations

import pytest

from app.domain.graph.domain_tag import detect_domain, parse_domain


def test_detect_cobranzas() -> None:
    assert detect_domain("¿Cómo es el handoff de cobranzas?") == "cobranzas"


def test_detect_tenela() -> None:
    assert detect_domain("¿Qué APIs tiene Tenela?") == "tenela"


def test_detect_general() -> None:
    assert detect_domain("hola") == "general"


def test_parse_override() -> None:
    assert parse_domain("Ventas") == "ventas"
    assert parse_domain("auto") is None
    assert parse_domain(None) is None


def test_parse_invalid() -> None:
    with pytest.raises(ValueError):
        parse_domain("marketing")
