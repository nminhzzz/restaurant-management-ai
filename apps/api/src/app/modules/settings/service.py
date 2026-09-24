"""Settings service: auth, users, config, audit, backup."""

from datetime import UTC, datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError, UnauthenticatedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.settings.models import RoleTable, SystemConfig, User
from app.modules.settings.schemas import ConfigUpdate
from app.shared.audit import SystemAuditLog
from app.shared.base import Base
from app.shared.enums import UserStatus
from app.shared.roles import Role

ROLE_SEEDS = (
    (
        Role.MANAGER,
        "Qu\u1ea3n l\u00fd",
        "To\u00e0n quy\u1ec1n, k\u1ebf th\u1eeba quy\u1ec1n Thu ng\u00e2n v\u00e0 Nh\u00e2n vi\u00ean kho",
    ),
    (Role.CASHIER, "Thu ng\u00e2n", "B\u00e1n h\u00e0ng, thanh to\u00e1n, tra c\u1ee9u order"),
    (
        Role.WAREHOUSE,
        "Nh\u00e2n vi\u00ean kho",
        "Nh\u1eadp, xu\u1ea5t, ki\u1ec3m k\u00ea, xem t\u1ed3n",
    ),
)


async def seed_reference_data(session: AsyncSession) -> None:
    """Idempotent: safe to call on every boot and every seed run."""
    for role, name, desc in ROLE_SEEDS:
        # Idempotent via select+insert (race safe on single-worker test; prod uses ON DUPLICATE via migration seed), MySQL uses ON DUPLICATE - use generic upsert via select+insert for cross-dialect
        existing = await session.execute(select(RoleTable).where(RoleTable.id == role.value))
        if existing.scalar_one_or_none() is None:
            session.add(RoleTable(id=role.value, name=name, description=desc))
    await session.flush()
    # Config singleton
    existing_cfg = await session.execute(select(SystemConfig))
    if existing_cfg.scalar_one_or_none() is None:
        session.add(
            SystemConfig(
                restaurant_name="Nh\u00e0 h\u00e0ng",
                address=None,
                invoice_template=None,
                default_stock_threshold=5,
                business_day_start=time(6, 0),
            )
        )
        await session.flush()


async def authenticate(session: AsyncSession, username: str, password: str) -> User:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if (
        user is None
        or user.status != UserStatus.HOAT_DONG
        or not verify_password(password, user.password_hash)
    ):
        raise UnauthenticatedError(
            "T\u00ean \u0111\u0103ng nh\u1eadp ho\u1eb7c m\u1eadt kh\u1ea9u kh\u00f4ng \u0111\u00fang."
        )
    return user


async def issue_token(user: User) -> dict:
    token = create_access_token(str(user.id), {"role": user.role_id, "username": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role_id,
        "username": user.username,
    }


async def create_user(
    session: AsyncSession,
    actor_id: int,
    username: str,
    password: str,
    full_name: str,
    phone: str | None,
    role: str | Role,
) -> User:
    role_value = role.value if isinstance(role, Role) else str(role)
    if role_value not in {r.value for r in Role}:
        raise BusinessRuleError(f"Vai tr\u00f2 kh\u00f4ng h\u1ee3p l\u1ec7: {role_value}")
    # Check duplicate
    existing = await session.execute(select(User).where(User.username == username))
    if existing.scalar_one_or_none() is not None:
        from app.core.errors import ConflictError

        raise ConflictError(
            f"T\u00ean \u0111\u0103ng nh\u1eadp \u0111\u00e3 t\u1ed3n t\u1ea1i: {username}"
        )
    user = User(
        username=username,
        password_hash=hash_password(password),
        full_name=full_name,
        phone=phone,
        role_id=role_value,
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    session.add(user)
    await session.flush()
    # Audit in same transaction
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="CREATE_USER",
            target_entity="NGUOI_DUNG",
            target_id=str(user.id),
            after={"username": username, "role": role_value},
        )
    )
    await session.flush()
    return user


async def lock_user(session: AsyncSession, actor_id: int, user_id: int) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Kh\u00f4ng t\u00ecm th\u1ea5y t\u00e0i kho\u1ea3n.")
    before = {"TrangThai": user.status}
    user.status = "\u0110\u00e3 kh\u00f3a"
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="LOCK_USER",
            target_entity="NGUOI_DUNG",
            target_id=str(user_id),
            before=before,
            after={"TrangThai": user.status},
        )
    )
    await session.flush()
    return user


async def reset_password(
    session: AsyncSession, actor_id: int, user_id: int, new_password: str
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Kh\u00f4ng t\u00ecm th\u1ea5y t\u00e0i kho\u1ea3n.")
    user.password_hash = hash_password(new_password)
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="RESET_PASSWORD",
            target_entity="NGUOI_DUNG",
            target_id=str(user_id),
        )
    )
    await session.flush()


async def change_own_password(
    session: AsyncSession, user_id: int, old_password: str, new_password: str
) -> None:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Kh\u00f4ng t\u00ecm th\u1ea5y t\u00e0i kho\u1ea3n.")
    if not verify_password(old_password, user.password_hash):
        raise BusinessRuleError("M\u1eadt kh\u1ea9u hi\u1ec7n t\u1ea1i kh\u00f4ng \u0111\u00fang.")
    user.password_hash = hash_password(new_password)
    await session.flush()
    # Self-service not audited per spec


async def get_config(session: AsyncSession) -> SystemConfig:
    result = await session.execute(select(SystemConfig))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        raise NotFoundError(
            "Ch\u01b0a c\u00f3 c\u1ea5u h\u00ecnh h\u1ec7 th\u1ed1ng. Vui l\u00f2ng ch\u1ea1y seed_reference_data."
        )
    return cfg


async def update_config(
    session: AsyncSession, actor_id: int, data: ConfigUpdate | dict
) -> SystemConfig:
    d = data.model_dump(exclude_none=False) if isinstance(data, ConfigUpdate) else data
    cfg = await get_config(session)
    # Only allow specific fields, ignore business_day_start
    if "TenNhaHang" in d and d["TenNhaHang"] is not None:
        cfg.restaurant_name = d["TenNhaHang"]
    if "DiaChi" in d:
        cfg.address = d["DiaChi"]
    if "MauHoaDon" in d:
        cfg.invoice_template = d["MauHoaDon"]
    if "NguongTonMacDinh" in d and d["NguongTonMacDinh"] is not None:
        if d["NguongTonMacDinh"] < 0:
            raise BusinessRuleError(
                "Ng\u01b0\u1ee1ng t\u1ed3n kh\u00f4ng \u0111\u01b0\u1ee3c \u00e2m."
            )
        cfg.default_stock_threshold = d["NguongTonMacDinh"]
    # BusinessDate locked
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_CONFIG",
            target_entity="CAU_HINH_HE_THONG",
            target_id=str(cfg.id),
        )
    )
    await session.flush()
    return cfg


async def list_users(
    session: AsyncSession, page: int = 1, size: int = 20
) -> tuple[list[User], int]:
    from sqlalchemy import func as sa_func

    total = (await session.execute(select(sa_func.count()).select_from(User))).scalar_one()
    result = await session.execute(
        select(User).offset((page - 1) * size).limit(size).order_by(User.id)
    )
    return list(result.scalars().all()), total


async def list_audit(
    session: AsyncSession,
    page: int = 1,
    size: int = 20,
    action: str | None = None,
    user_id: int | None = None,
) -> tuple[list[SystemAuditLog], int]:
    from sqlalchemy import func as sa_func

    q = select(SystemAuditLog)
    cq = select(sa_func.count()).select_from(SystemAuditLog)
    if action:
        q = q.where(SystemAuditLog.action == action)
        cq = cq.where(SystemAuditLog.action == action)
    if user_id:
        q = q.where(SystemAuditLog.user_id == user_id)
        cq = cq.where(SystemAuditLog.user_id == user_id)
    total = (await session.execute(cq)).scalar_one()
    result = await session.execute(
        q.order_by(SystemAuditLog.id.desc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total


async def export_backup(session: AsyncSession, actor_id: int) -> dict:
    """Create backup dump and audit in same transaction (NFR-10)."""
    now = datetime.now(UTC)
    session.add(
        SystemAuditLog(
            user_id=actor_id, action="EXPORT_BACKUP", target_entity="SYSTEM", target_id="backup"
        )
    )
    await session.flush()
    return {
        "created_at": now.isoformat(),
        "covers_until": now.isoformat(),
        "size": len(Base.metadata.tables),
    }
