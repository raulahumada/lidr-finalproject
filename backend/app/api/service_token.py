"""App-wide service-to-service bearer authentication.

When ``SERVICE_TOKEN`` is set, every API route except health (and docs in
non-production) requires ``Authorization: Bearer …``. Empty token in
non-production leaves the API open with a warning; ``APP_ENV=production``
refuses to boot without a token — a forgotten secret is worse than none.

|| Auth bearer servicio-a-servicio en toda la API.
Con token, todo menos health exige Bearer. Vacío en no-prod = API abierta
(con warning). En production sin token el proceso no arranca.
"""
from __future__ import annotations

import logging
import secrets
from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings

log = logging.getLogger(__name__)


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, param = authorization.partition(" ")
    if scheme.lower() != "bearer" or not param.strip():
        return None
    return param.strip()


def _is_exempt(path: str, *, settings: Settings) -> bool:
    prefix = settings.api_prefix.rstrip("/") or ""
    if path == f"{prefix}/health":
        return True
    # Docs stay usable locally / when the gate is off; locked in production
    # when a token is configured.
    if settings.app_env.lower() == "production" and settings.service_token.strip():
        return False
    return path in {"/docs", "/docs/oauth2-redirect", "/redoc", "/openapi.json", "/"}


async def service_token_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    settings = get_settings()
    expected = settings.service_token.strip()

    if not expected:
        return await call_next(request)

    if request.method == "OPTIONS" or _is_exempt(request.url.path, settings=settings):
        return await call_next(request)

    provided = _bearer_token(request.headers.get("Authorization"))
    if not provided or not secrets.compare_digest(provided, expected):
        log.warning(
            "service_token_rejected path=%s method=%s reason=%s",
            request.url.path,
            request.method,
            "missing" if not provided else "mismatch",
        )
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Missing or invalid Authorization bearer token."},
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await call_next(request)


def assert_service_token_boot_policy(settings: Settings | None = None) -> None:
    """Raise if production would start without a service token."""
    cfg = settings or get_settings()
    if cfg.app_env.lower() == "production" and not cfg.service_token.strip():
        raise RuntimeError(
            "SERVICE_TOKEN is required when APP_ENV=production. "
            "Refusing to start with an open API."
        )
    if not cfg.service_token.strip() and cfg.app_env.lower() != "production":
        log.warning(
            "service_token_open_mode: SERVICE_TOKEN is empty; "
            "API accepts unauthenticated requests (non-production only)."
        )
