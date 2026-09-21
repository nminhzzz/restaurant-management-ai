"""Domain errors and the handlers that turn them into API responses.

Messages are Vietnamese because they are surfaced to end users (NFR-14);
internal details are never leaked (rule 5).
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


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


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )
