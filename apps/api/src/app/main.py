"""FastAPI application factory."""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, validate_runtime_settings
from app.core.errors import register_error_handlers
from app.modules.ai.pipeline import executor
from app.modules.ai.router import router as ai_router
from app.modules.catalog.router import router as catalog_router
from app.modules.inventory.router import router as inventory_router
from app.modules.reports.router import router as reports_router
from app.modules.sales import payments
from app.modules.sales.printing import print_queue_loop
from app.modules.sales.router import router as sales_router
from app.modules.settings.router import router as settings_router

logger = logging.getLogger(__name__)

MODULE_ROUTERS = (
    catalog_router,
    sales_router,
    inventory_router,
    reports_router,
    settings_router,
    ai_router,
)


async def _expire_qr_loop() -> None:
    """FR-SALE-14: sweep expired QR payments even when no till is watching them."""
    interval = get_settings().payment_qr_expiry_interval_seconds
    if interval <= 0:
        return
    while True:
        await asyncio.sleep(interval)
        try:
            await payments.expire_qr_tick()
        except Exception:
            logger.exception("Could not expire stale QR payments")


async def _sepay_sync_loop() -> None:
    """Catch transfers that arrived while the API was down or without a webhook."""
    interval = get_settings().sepay_poll_interval_seconds
    if interval <= 0 or get_settings().payment_gateway != "sepay":
        return
    while True:
        try:
            await payments.sync_recent_transfers()
        except Exception:
            logger.exception("Could not sync recent SePay transfers")
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    tasks = [
        asyncio.create_task(_expire_qr_loop()),
        asyncio.create_task(print_queue_loop()),
        asyncio.create_task(_sepay_sync_loop()),
    ]
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
        for task in tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        await executor.dispose_engines()


def _mask_account(account: str) -> str | None:
    """Show which account receives money without disclosing it in logs/health."""
    digits = account.strip()
    if not digits:
        return None
    return f"***{digits[-4:]}" if len(digits) > 4 else "***"


def create_app() -> FastAPI:
    settings = get_settings()
    validate_runtime_settings(settings)
    app = FastAPI(
        lifespan=lifespan,
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
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )
    register_error_handlers(app)

    for router in MODULE_ROUTERS:
        app.include_router(router, prefix=settings.api_prefix)

    @app.get("/health", tags=["System"])
    async def health() -> dict[str, object]:
        gateway = settings.payment_gateway
        return {
            "status": "ok",
            "environment": settings.environment,
            "payment": {
                "gateway": gateway,
                "bank_code": settings.sepay_bank_code or None,
                "bank_account": _mask_account(settings.sepay_bank_account),
                "webhook_configured": bool(settings.sepay_webhook_api_key),
                "live": gateway == "sepay"
                and bool(settings.sepay_bank_account and settings.sepay_webhook_api_key),
            },
        }

    return app


app = create_app()
