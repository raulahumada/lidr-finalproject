"""Aggregate HTTP routers under the API prefix.

Routers stay transport-only; business wiring lives in ``dependencies`` /
``domain``.

|| Agrega los routers HTTP bajo el prefijo de API.
Los routers se quedan solo como transporte; el cableado de negocio vive en
``dependencies`` / ``domain``.
"""

from fastapi import APIRouter

from app.api.routes import (
    answer,
    answer_agentic,
    answer_agents,
    answer_session,
    config_models,
    health,
    ingest,
    search,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(search.router)
api_router.include_router(ingest.router)
api_router.include_router(config_models.router)
api_router.include_router(answer.router)
api_router.include_router(answer_agentic.router)
api_router.include_router(answer_agents.router)
api_router.include_router(answer_session.router)
api_router.include_router(answer_session.list_router)
