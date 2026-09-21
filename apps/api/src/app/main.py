"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.modules.ai.router import router as ai_router
from app.modules.catalog.router import router as catalog_router
from app.modules.inventory.router import router as inventory_router
from app.modules.reports.router import router as reports_router
from app.modules.sales.router import router as sales_router
from app.modules.settings.router import router as settings_router

MODULE_ROUTERS = (
    catalog_router,
    sales_router,
    inventory_router,
    reports_router,
    settings_router,
    ai_router,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Restaurant Management API",
        description=(
            "Backend for the AI-powered restaurant management system. "
            "Module boundaries follow the feature list in docs/."
        ),
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)

    for router in MODULE_ROUTERS:
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["System"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
