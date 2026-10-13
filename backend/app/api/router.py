from fastapi import APIRouter

from app.api.routes import answer, answer_agentic, answer_session, health, items, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(items.router)
api_router.include_router(search.router)
api_router.include_router(answer.router)
api_router.include_router(answer_agentic.router)
api_router.include_router(answer_session.router)
api_router.include_router(answer_session.list_router)
