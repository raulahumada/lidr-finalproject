from __future__ import annotations

from app.domain.graph.agents.intent_framer import intent_framer
from app.generation.conversation.anchors import (
    detect_anchors,
    is_scope_pin_only,
    pinned_domain,
)
from app.generation.conversation.budget import render_memory
from app.generation.conversation.facts import facts_from_turn
from app.generation.conversation.models import ConversationFacts, merge_anchors


def test_facts_merge_accumulates_and_replaces_last_docs() -> None:
    base = ConversationFacts(
        domains=["cobranzas"],
        entities=["tenela"],
        last_document_ids=["10"],
    )
    update = facts_from_turn(
        question="¿y el handoff por WhatsApp?",
        domain="operacion",
        citations=[{"document_id": 22}, {"document_id": "22"}],
    )
    merged = base.merge_with(update)
    assert merged.domains == ["cobranzas", "operacion"]
    assert "whatsapp" in merged.entities
    assert "tenela" in merged.entities
    assert merged.last_document_ids == ["22"]

    empty_cite = facts_from_turn(
        question="seguí",
        domain="general",
        citations=[],
    )
    kept = merged.merge_with(empty_cite)
    assert kept.last_document_ids == ["22"]


def test_detect_anchors_requires_scoping_phrase() -> None:
    assert detect_anchors("¿Cómo es el handoff de cobranzas?") == []
    pinned = detect_anchors(
        "De acá en adelante, solo cobranzas para las próximas preguntas"
    )
    assert len(pinned) == 1
    assert pinned[0].kind == "domain"
    assert pinned[0].value == "cobranzas"


def test_detect_anchors_solo_domain() -> None:
    pinned = detect_anchors("Solo en ventas, ¿cómo es la captación?")
    assert len(pinned) == 1
    assert pinned[0].value == "ventas"


def test_scoping_without_pinable_domain_is_noop() -> None:
    assert detect_anchors("De acá en adelante sé más breve") == []


def test_pinned_domain_prefers_latest() -> None:
    first = detect_anchors("De acá en adelante cobranzas")
    second = detect_anchors("Limitate solo a tenela")
    merged = merge_anchors(first, second)
    assert pinned_domain(merged) == "tenela"


def test_render_memory_includes_anchors() -> None:
    facts = ConversationFacts(domains=["cobranzas"], last_document_ids=["9"])
    anchors = detect_anchors("De ahora en más, solo cobranzas")
    block = render_memory(
        [{"question": "q", "answer": "a"}],
        budget=1024,
        facts=facts,
        anchors=anchors,
    )
    assert block is not None
    assert "cobranzas" in block.text
    assert "Alcance fijado" in block.text
    assert "Hechos de la sesión" in block.text


def test_render_memory_facts_only_without_window() -> None:
    facts = ConversationFacts(entities=["tenela"])
    block = render_memory([], budget=256, facts=facts, anchors=[])
    assert block is not None
    assert "tenela" in block.text


def test_scope_pin_only_vs_pin_plus_question() -> None:
    assert is_scope_pin_only("De aca en adelante solo hablemos de cobranzas")
    assert not is_scope_pin_only(
        "De acá en adelante solo cobranzas, ¿cómo es el handoff con Tenela?"
    )


def test_intent_framer_scope_pin_skips_rag_compose() -> None:
    out = intent_framer(
        {
            "question": "De aca en adelante solo hablemos de cobranzas",
            "domain": "general",
            "agent_trace": [],
        }
    )
    assert out["scope_pin_only"] is True
    assert out["domain"] == "cobranzas"
    assert "cobranzas" in out["answer"].lower()
    assert "handoff" not in out["answer"].lower()
    assert out["citations"] == []
    assert out["confidence"] == 1.0
