from fastapi import APIRouter

from app.api.routes import answer, health, items, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(items.router)
api_router.include_router(search.router)
api_router.include_router(answer.router)
