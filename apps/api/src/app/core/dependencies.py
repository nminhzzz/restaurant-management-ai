"""Reusable FastAPI dependencies: authentication and role authorisation.

Authorisation is enforced here, at the API layer, not in the UI (NFR-05).
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import ForbiddenError, UnauthenticatedError
from app.core.security import decode_access_token
from app.shared.roles import Role

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """The authenticated caller. Will be backed by the NGUOI_DUNG entity once
    the settings module is implemented."""

    user_id: int
    username: str
    role: Role


async def get_current_user(
    scheme: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if scheme is None:
        raise UnauthenticatedError("Vui lòng đăng nhập để tiếp tục.")

    claims = decode_access_token(scheme.credentials)
    try:
        return Principal(
            user_id=int(str(claims["sub"])),
            username=str(claims.get("username", "")),
            role=Role(str(claims["role"])),
        )
    except (KeyError, ValueError) as exc:
        raise UnauthenticatedError("Phiên đăng nhập không hợp lệ.") from exc


CurrentUser = Annotated[Principal, Depends(get_current_user)]


def require_roles(*allowed: Role) -> Callable[[Principal], Coroutine[Any, Any, Principal]]:
    """Guard factory used by routers to restrict an endpoint to some roles."""

    async def _guard(user: CurrentUser) -> Principal:
        if user.role not in allowed:
            raise ForbiddenError("Bạn không có quyền thực hiện chức năng này.")
        return user

    return _guard


def require_any_role(*roles: Role) -> Callable[[Principal], Coroutine[Any, Any, Principal]]:
    """Manager inherits all: allow if role is MANAGER or in allowed."""

    async def _guard(user: CurrentUser) -> Principal:
        if user.role == Role.MANAGER:
            import logging

            logging.getLogger(__name__).info(
                "manager bypass role check user=%s allowed=%s", user.user_id, roles
            )
            return user
        if user.role not in roles:
            raise ForbiddenError(
                "B\u1ea1n kh\u00f4ng c\u00f3 quy\u1ec1n th\u1ef1c hi\u1ec7n ch\u1ee9c n\u0103ng n\u00e0y."
            )
        return user

    return _guard
