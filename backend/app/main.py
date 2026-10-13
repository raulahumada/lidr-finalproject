from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.api.service_token import assert_service_token_boot_policy, service_token_middleware
from app.config import get_settings
from app.domain.graph.checkpointer import close_checkpointer, open_checkpointer


@asynccontextmanager
async def lifespan(_app: FastAPI):
    open_checkpointer()
    try:
        yield
    finally:
        close_checkpointer()


def create_app() -> FastAPI:
    settings = get_settings()
    assert_service_token_boot_policy(settings)

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Starlette: last added runs first. Token check should run before CORS
    # response short-circuits on failures; add after CORS so CORS wraps it.
    app.middleware("http")(service_token_middleware)

    app.include_router(api_router, prefix=settings.api_prefix)

    @app.get("/")
    def root() -> dict[str, str]:
        return {
            "message": f"Welcome to {settings.app_name}",
            "docs": "/docs",
            "health": f"{settings.api_prefix}/health",
        }

    return app


app = create_app()
