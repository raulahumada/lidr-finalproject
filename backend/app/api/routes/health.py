"""Liveness probe — the only route left open when ``SERVICE_TOKEN`` is set.

Railway (and Compose) hit this path; it must never require a bearer.

|| Probe de vida — la única ruta abierta cuando hay ``SERVICE_TOKEN``.
Railway (y Compose) pegan acá; no debe exigir bearer.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.app_name,
        "env": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
