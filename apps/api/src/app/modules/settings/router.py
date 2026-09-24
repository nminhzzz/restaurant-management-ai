"""HTTP layer for the settings module."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.dependencies import (
    Principal,
    get_current_user,
    require_roles,
)
from app.core.errors import BusinessRuleError, UnauthenticatedError
from app.modules.settings import service as svc
from app.modules.settings.schemas import (
    AuditEntryOut,
    BackupDump,
    ChangePasswordRequest,
    ConfigOut,
    ConfigUpdate,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserOut,
)
from app.shared.pagination import Page
from app.shared.roles import Role

router = APIRouter(prefix="/settings", tags=["Module 5 — Settings"])


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    user = await svc.authenticate(session, payload.username, payload.password)
    tok = await svc.issue_token(user)
    return tok


@router.get("/auth/me", response_model=UserOut)
async def me(
    user: Principal = Depends(get_current_user), session: AsyncSession = Depends(get_session)
):
    from sqlalchemy import select

    from app.modules.settings.models import User

    result = await session.execute(select(User).where(User.id == user.user_id))
    u = result.scalar_one_or_none()
    if u is None:
        raise UnauthenticatedError("T\u00e0i kho\u1ea3n kh\u00f4ng t\u1ed3n t\u1ea1i.")
    return UserOut.model_validate(u)


@router.get("/users", response_model=Page[UserOut])
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> Page[UserOut]:
    # MANAGER only; require_roles will check
    # But spec says MANAGER inherits, so need require_any_role for other endpoints; for users MANAGER only
    items, total = await svc.list_users(session, page, size)
    return Page[UserOut](
        items=[UserOut.model_validate(x) for x in items], total=total, page=page, size=size
    )


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    payload: UserCreate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    u = await svc.create_user(
        session,
        user.user_id,
        payload.username,
        payload.password,
        payload.full_name,
        payload.phone,
        payload.role,
    )
    await session.commit()
    return UserOut.model_validate(u)


@router.patch("/users/{user_id}/lock", response_model=UserOut)
async def lock_user(
    user_id: int,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    u = await svc.lock_user(session, user.user_id, user_id)
    await session.commit()
    return UserOut.model_validate(u)


@router.post("/users/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> None:
    await svc.reset_password(session, user.user_id, user_id, payload.new_password)
    await session.commit()


@router.post("/auth/change-password", status_code=204)
async def change_password(
    payload: ChangePasswordRequest,
    user: Principal = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    if payload.old_password == payload.new_password:
        raise BusinessRuleError(
            "M\u1eadt kh\u1ea9u m\u1edbi ph\u1ea3i kh\u00e1c m\u1eadt kh\u1ea9u c\u0169."
        )
    await svc.change_own_password(session, user.user_id, payload.old_password, payload.new_password)
    await session.commit()


@router.get("/config", response_model=ConfigOut)
async def get_config(
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> ConfigOut:
    cfg = await svc.get_config(session)
    return ConfigOut.model_validate(cfg)


@router.put("/config", response_model=ConfigOut)
async def update_config(
    payload: ConfigUpdate,
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> ConfigOut:
    cfg = await svc.update_config(session, user.user_id, payload)
    await session.commit()
    return ConfigOut.model_validate(cfg)


@router.get("/audit-log", response_model=Page[AuditEntryOut])
async def audit_log(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    action: str | None = Query(None),
    user_id: int | None = Query(None),
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> Page[AuditEntryOut]:
    items, total = await svc.list_audit(session, page, size, action, user_id)
    return Page[AuditEntryOut](
        items=[AuditEntryOut.model_validate(x) for x in items], total=total, page=page, size=size
    )


@router.post("/backup", response_model=BackupDump)
async def backup(
    user: Principal = Depends(require_roles(Role.MANAGER)),
    session: AsyncSession = Depends(get_session),
) -> BackupDump:
    dump = await svc.export_backup(session, user.user_id)
    await session.commit()
    return BackupDump(**dump)
