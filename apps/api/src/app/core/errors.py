"""Domain errors and the handlers that turn them into API responses.

Messages are Vietnamese because they are surfaced to end users (NFR-14);
internal details are never leaked (rule 5).
"""

import json
import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

logger = logging.getLogger("app.errors")

INTERNAL_ERROR_MESSAGE = "Hệ thống gặp lỗi khi xử lý yêu cầu. Vui lòng thử lại sau."
_BODY_LIMIT = 4096
# Request fields whose value must never reach a log file.
_MASKED_KEYS = ("password", "mat_khau", "matkhau", "token", "secret", "api_key")


class AppError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "APP_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class BusinessRuleError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    code = "BUSINESS_RULE_VIOLATION"


class UnauthenticatedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHENTICATED"


class RequestBodyCapture:
    """Keep the first few KB of each request body so an error log can show the input.

    Pure ASGI (not BaseHTTPMiddleware) so the body stream reaches the route untouched.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        captured = bytearray()
        scope.setdefault("state", {})["body_excerpt"] = captured

        async def recording_receive() -> Message:
            message = await receive()
            if message["type"] == "http.request" and len(captured) < _BODY_LIMIT:
                captured.extend(message.get("body", b"")[: _BODY_LIMIT - len(captured)])
            return message

        await self.app(scope, recording_receive, send)


def _mask(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if any(m in key.lower() for m in _MASKED_KEYS) else _mask(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_mask(item) for item in value]
    return value


def _describe(request: Request) -> str:
    """Operation and input of the failing request, with credentials masked (NFR-15)."""
    operation = f"{request.method} {request.url.path}"
    if request.url.query:
        operation += f"?{request.url.query}"
    raw = bytes(request.scope.get("state", {}).get("body_excerpt", b""))
    if not raw:
        return operation
    try:
        body = json.dumps(_mask(json.loads(raw)), ensure_ascii=False)
    except ValueError:
        body = f"<{len(raw)} bytes, not JSON>"
    return f"{operation} body={body}"


def register_error_handlers(app: FastAPI) -> None:
    app.add_middleware(RequestBodyCapture)

    @app.exception_handler(AppError)
    async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        # Expected refusals are worth a trace too: they are what users report as bugs.
        logger.warning("%s %s: %s", exc.code, _describe(request), exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # The id ties the user's report to this log line without exposing internals.
        error_id = uuid.uuid4().hex[:12]
        logger.error("INTERNAL_ERROR id=%s %s", error_id, _describe(request), exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": INTERNAL_ERROR_MESSAGE,
                    "error_id": error_id,
                }
            },
        )
