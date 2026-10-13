from __future__ import annotations

from eval.scoring import score_case, score_multiturn_turn


def test_citations_expected_pass() -> None:
    result = score_case(
        {"id": "c1", "expect_citations": True},
        {
            "status": "completed",
            "answer": "Tenela integra cobranzas.",
            "citations": [{"chunk_id": 1}],
            "citations_valid": True,
            "no_evidence": False,
        },
    )
    assert result["passed"] is True


def test_citations_expected_fail_empty() -> None:
    result = score_case(
        {"id": "c1", "expect_citations": True},
        {
            "status": "completed",
            "answer": "hola",
            "citations": [],
            "citations_valid": True,
        },
    )
    assert result["passed"] is False
    assert any("citations" in r for r in result["reasons"])


def test_citations_valid_false_fails() -> None:
    result = score_case(
        {"id": "c1", "expect_citations": True},
        {
            "status": "completed",
            "answer": "x",
            "citations": [{"chunk_id": 1}],
            "citations_valid": False,
        },
    )
    assert result["passed"] is False


def test_must_mention_and_forbidden() -> None:
    ok = score_case(
        {
            "id": "c2",
            "must_mention": ["Tenela"],
            "must_not_mention": ["/v9/magic"],
        },
        {"status": "completed", "answer": "Flujo con Tenela y WhatsApp."},
    )
    assert ok["passed"] is True

    bad = score_case(
        {
            "id": "c2",
            "must_mention": ["Tenela"],
            "must_not_mention": ["/v9/magic"],
        },
        {
            "status": "completed",
            "answer": "Usá POST /v9/magic para el préstamo.",
        },
    )
    assert bad["passed"] is False
    assert len(bad["reasons"]) >= 2



def test_expect_pause_uses_pause_status() -> None:
    result = score_case(
        {"id": "c3", "expect_pause": True},
        {"status": "completed", "answer": "ok"},
        pause_status="awaiting_human_review",
    )
    assert result["passed"] is True

    fail = score_case(
        {"id": "c3", "expect_pause": True},
        {"status": "completed", "answer": "ok"},
        pause_status="completed",
    )
    assert fail["passed"] is False


def test_expect_no_evidence() -> None:
    result = score_case(
        {"id": "c4", "expect_no_evidence": True},
        {
            "status": "awaiting_human_review",
            "answer": "No hay evidencia suficiente.",
            "citations": [],
            "no_evidence": True,
        },
    )
    assert result["passed"] is True


def test_multiturn_expect_rewrite_false_negative() -> None:
    written = "¿y con Tenela?"
    fail = score_multiturn_turn(
        {
            "id": "t1",
            "question": written,
            "expect_rewrite": True,
            "expect_citations": True,
        },
        {
            "status": "completed",
            "answer": "Tenela.",
            "citations": [{"chunk_id": 1}],
            "citations_valid": True,
            "resolved_question": written,
        },
        written_question=written,
    )
    assert fail["passed"] is False
    assert any("rewrite" in r for r in fail["reasons"])

    missing = score_multiturn_turn(
        {"question": written, "expect_rewrite": True},
        {"status": "completed", "answer": "x", "resolved_question": None},
        written_question=written,
    )
    assert missing["passed"] is False
    assert any("rewrite" in r for r in missing["reasons"])


def test_multiturn_expect_rewrite_pass_and_contains() -> None:
    written = "¿y con Tenela?"
    resolved = "¿y con Tenela? (sobre handoff de cobranzas)"
    ok = score_multiturn_turn(
        {
            "question": written,
            "expect_rewrite": True,
            "expect_resolved_contains": ["handoff"],
            "expect_citations": True,
            "must_mention": ["tenela"],
        },
        {
            "status": "completed",
            "answer": "Handoff con Tenela.",
            "citations": [{"chunk_id": 1}],
            "citations_valid": True,
            "resolved_question": resolved,
        },
        written_question=written,
    )
    assert ok["passed"] is True


def test_multiturn_no_rewrite_expected() -> None:
    q = "¿Cómo se verifica la identidad en Tenela?"
    result = score_multiturn_turn(
        {"question": q, "expect_rewrite": False, "expect_citations": True},
        {
            "status": "completed",
            "answer": "Identidad en Tenela.",
            "citations": [{"chunk_id": 2}],
            "citations_valid": True,
            "resolved_question": None,
        },
        written_question=q,
    )
    assert result["passed"] is True
