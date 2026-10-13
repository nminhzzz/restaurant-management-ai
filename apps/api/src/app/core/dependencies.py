"""Reusable FastAPI dependencies: authentication and role authorisation.

Authorisation is enforced here, at the API layer, not in the UI (NFR-05).
The bearer token only identifies the account; its status and role are read from the
database on every request so that a locked or demoted account loses access at once
(NFR-19, FR-SET-01).
"""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.errors import ForbiddenError, UnauthenticatedError
from app.core.security import decode_access_token
from app.modules.settings.models import User
from app.shared.enums import UserStatus
from app.shared.roles import Role

_bearer = HTTPBearer(auto_error=False)
_INVALID_SESSION = "Phiên đăng nhập không hợp lệ hoặc tài khoản không còn hiệu lực."


@dataclass(frozen=True)
class Principal:
    """The authenticated caller, as stored in NGUOI_DUNG at the time of the request."""

    user_id: int
    username: str
    role: Role


async def get_current_user(
    scheme: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Principal:
    if scheme is None:
        raise UnauthenticatedError("Vui lòng đăng nhập để tiếp tục.")

    try:
        user_id = int(str(decode_access_token(scheme.credentials)["sub"]))
    except (KeyError, ValueError, InvalidTokenError) as exc:
        raise UnauthenticatedError(_INVALID_SESSION) from exc

    # Selecting columns (not the entity) bypasses the identity map, so a status
    # or role changed by another transaction is always seen.
    row = (
        await session.execute(
            select(User.username, User.role_id, User.status).where(User.id == user_id)
        )
    ).one_or_none()
    if row is None or row.status != UserStatus.HOAT_DONG:
        raise UnauthenticatedError(_INVALID_SESSION)
    try:
        role = Role(row.role_id)
    except ValueError as exc:
        raise UnauthenticatedError(_INVALID_SESSION) from exc
    return Principal(user_id=user_id, username=row.username, role=role)


CurrentUser = Annotated[Principal, Depends(get_current_user)]


def require_roles(*allowed: Role) -> Callable[[Principal], Coroutine[Any, Any, Principal]]:
    """Guard factory used by routers to restrict an endpoint to some roles."""

    async def _guard(user: CurrentUser) -> Principal:
        if user.role not in allowed:
            raise ForbiddenError("Bạn không có quyền thực hiện chức năng này.")
        return user

    return _guard
