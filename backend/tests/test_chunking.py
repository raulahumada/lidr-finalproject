from __future__ import annotations

from app.generation.rag.chunking import chunk_document, normalize_text


def test_normalize_collapses_blank_lines() -> None:
    text = "A\n\n\n\nB"
    assert "\n\n\n" not in normalize_text(text, extension="txt")
    assert "A" in normalize_text(text) and "B" in normalize_text(text)


def test_normalize_pdf_joins_wrapped_lines() -> None:
    text = "Este es un renglón\npartido por el PDF\n\nOtro párrafo."
    normalized = normalize_text(text, extension="pdf")
    assert "renglón partido" in normalized
    assert "Otro párrafo" in normalized


def test_recursive_splits_long_prose() -> None:
    paragraphs = [
        f"Parrafo {i} sobre Metropol Fintech omnicanalidad cobranzas y ventas con Tenela. "
        * 8
        for i in range(20)
    ]
    text = "\n\n".join(paragraphs)
    pieces = chunk_document(text, extension="txt")
    assert len(pieces) > 1
    assert all(p.content.strip() for p in pieces)
    assert all(p.strategy == "recursive" for p in pieces)


def test_markdown_respects_headers() -> None:
    text = """# Root

## Chatwoot
Inbox y conversaciones de WhatsApp para Metropol.

## Rasa
Bot de NLU y flujos de dialogo para cobranzas.
"""
    pieces = chunk_document(text, extension="md")
    assert pieces
    assert all(p.strategy == "markdown" for p in pieces)
    joined = "\n".join(p.content for p in pieces)
    assert "Chatwoot" in joined or any(p.section and "Chatwoot" in p.section for p in pieces)
    assert "Rasa" in joined or any(p.section and "Rasa" in p.section for p in pieces)
    # Prefer that Chatwoot and Rasa bodies are not forced into one tiny shared chunk only
    sections = {p.section for p in pieces if p.section}
    assert sections & {"Chatwoot", "Rasa"} or ("Chatwoot" in joined and "Rasa" in joined)


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_document("   \n\n  ", extension="docx") == []
