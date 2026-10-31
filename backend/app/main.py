from fastapi import FastAPI

from app.api import health
from app.core.config import get_settings


def create_app() -> FastAPI:
    # Every route lives under /api: Caddy sends /api/* here and serves the SPA for everything else.
    app = FastAPI(
        title=f"{get_settings().app_name} API",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.include_router(health.router, prefix="/api")
    return app


app = create_app()
