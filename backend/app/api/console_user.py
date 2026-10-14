"""Read console operator id from the BFF-forwarded header.

``X-Console-User`` scopes conversation sessions to the operator. Trust is
acceptable because only the BFF (holding ``SERVICE_TOKEN``) can call the API
successfully when the token is configured.

|| Lee el id del operador desde el header que reenvía el BFF.
``X-Console-User`` acota las sesiones de chat al dueño.
"""
from __future__ import annotations

from fastapi import Header

CONSOLE_USER_HEADER = "X-Console-User"
MAX_OWNER_ID_CHARS = 64


def parse_console_user_id(raw: str | None) -> str | None:
    """Normalize header value; drop empty or over-long ids (never truncate)."""
    if raw is None:
        return None
    trimmed = raw.strip()
    if not trimmed or len(trimmed) > MAX_OWNER_ID_CHARS:
        return None
    return trimmed


def get_console_user_id(
    x_console_user: str | None = Header(default=None, alias=CONSOLE_USER_HEADER),
) -> str | None:
    return parse_console_user_id(x_console_user)
