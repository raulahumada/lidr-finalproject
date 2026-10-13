from app.api.console_user import parse_console_user_id


def test_parse_console_user_empty() -> None:
    assert parse_console_user_id(None) is None
    assert parse_console_user_id("") is None
    assert parse_console_user_id("   ") is None


def test_parse_console_user_trims() -> None:
    assert parse_console_user_id("  user-abc  ") == "user-abc"


def test_parse_console_user_drops_overlong() -> None:
    assert parse_console_user_id("x" * 65) is None
    assert parse_console_user_id("x" * 64) == "x" * 64
