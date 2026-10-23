"""Settings service: auth, users, config, audit, backup."""

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BusinessRuleError, NotFoundError, UnauthenticatedError
from app.core.security import create_access_token, hash_password, verify_password
from app.modules.settings.models import BusinessDateCutoff, RoleTable, SystemConfig, User
from app.modules.settings.schemas import ConfigUpdate
from app.shared import business_date
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
                expiry_warning_days=3,
                hold_minutes=5,
                ai_daily_question_quota=50,
            )
        )
        await session.flush()

    # Preserve the original cutoff as the history baseline.
    if await session.get(BusinessDateCutoff, date(1000, 1, 1)) is None:
        cfg = (await session.scalars(select(SystemConfig))).one()
        session.add(
            BusinessDateCutoff(
                effective_date=date(1000, 1, 1),
                start_time=cfg.business_day_start,
                starts_at=datetime.combine(date(1000, 1, 1), cfg.business_day_start),
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
    token = create_access_token(
        str(user.id),
        {"role": user.role_id, "username": user.username, "ver": user.token_version},
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role_id,
        "username": user.username,
    }


async def create_user(
    session: AsyncSession,
    actor_id: int | None,
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


async def _set_user_status(
    session: AsyncSession, actor_id: int, user_id: int, status: str, action: str
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Kh\u00f4ng t\u00ecm th\u1ea5y t\u00e0i kho\u1ea3n.")
    before = {"TrangThai": user.status}
    user.status = status
    if status != UserStatus.HOAT_DONG:
        # Locking revokes tokens issued while the account was still active.
        user.token_version = int(user.token_version or 0) + 1
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action=action,
            target_entity="NGUOI_DUNG",
            target_id=str(user_id),
            before=before,
            after={"TrangThai": user.status},
        )
    )
    await session.flush()
    return user


async def lock_user(session: AsyncSession, actor_id: int, user_id: int) -> User:
    # Locking yourself could leave the restaurant with no manager able to log in.
    if actor_id == user_id:
        raise BusinessRuleError(
            "Kh\u00f4ng th\u1ec3 t\u1ef1 kh\u00f3a t\u00e0i kho\u1ea3n c\u1ee7a ch\u00ednh m\u00ecnh."
        )
    return await _set_user_status(session, actor_id, user_id, "\u0110\u00e3 kh\u00f3a", "LOCK_USER")


async def unlock_user(session: AsyncSession, actor_id: int, user_id: int) -> User:
    return await _set_user_status(
        session, actor_id, user_id, "Ho\u1ea1t \u0111\u1ed9ng", "UNLOCK_USER"
    )


async def update_user(
    session: AsyncSession,
    actor_id: int,
    user_id: int,
    *,
    full_name: str | None = None,
    phone: str | None = None,
    role: str | Role | None = None,
) -> User:
    """FR-SET-01: edit the display fields and assign one of the three roles."""
    user = await session.get(User, user_id)
    if user is None:
        raise NotFoundError("Kh\u00f4ng t\u00ecm th\u1ea5y t\u00e0i kho\u1ea3n.")
    before = {"HoTen": user.full_name, "SoDienThoai": user.phone, "MaVaiTro": user.role_id}
    if full_name is not None:
        user.full_name = full_name
    if phone is not None:
        user.phone = phone
    if role is not None:
        role_value = role.value if isinstance(role, Role) else str(role)
        if role_value not in {r.value for r in Role}:
            raise BusinessRuleError(f"Vai tr\u00f2 kh\u00f4ng h\u1ee3p l\u1ec7: {role_value}")
        if actor_id == user_id and role_value != Role.MANAGER.value:
            raise BusinessRuleError(
                "Kh\u00f4ng th\u1ec3 t\u1ef1 b\u1ecf quy\u1ec1n qu\u1ea3n l\u00fd."
            )
        if user.role_id == Role.MANAGER.value and role_value != Role.MANAGER.value:
            managers = (
                (
                    await session.execute(
                        select(User).where(
                            User.role_id == Role.MANAGER.value,
                            User.status == UserStatus.HOAT_DONG,
                        )
                    )
                )
                .scalars()
                .all()
            )
            if len(managers) <= 1:
                raise BusinessRuleError(
                    "Ph\u1ea3i c\u00f2n \u00edt nh\u1ea5t m\u1ed9t qu\u1ea3n l\u00fd ho\u1ea1t \u0111\u1ed9ng."
                )
        if user.role_id != role_value:
            # A role change invalidates the old token's embedded role.
            user.token_version = int(user.token_version or 0) + 1
        user.role_id = role_value
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_USER",
            target_entity="NGUOI_DUNG",
            target_id=str(user_id),
            before=before,
            after={"HoTen": user.full_name, "SoDienThoai": user.phone, "MaVaiTro": user.role_id},
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
    # Every JWT issued before this moment stops working.
    user.token_version = int(user.token_version or 0) + 1
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
    # Every JWT issued before this moment stops working.
    user.token_version = int(user.token_version or 0) + 1
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
    session: AsyncSession, actor_id: int | None, data: ConfigUpdate | dict
) -> SystemConfig:
    payload = data if isinstance(data, ConfigUpdate) else ConfigUpdate.model_validate(data)
    d = payload.model_dump(exclude_unset=True)
    # Serialize concurrent edits so they cannot choose inconsistent effective dates.
    cfg = (await session.scalars(select(SystemConfig).with_for_update())).one()
    before_schedule = await business_date.load_business_date_schedule(session)
    before: dict[str, object] = {
        "TenNhaHang": cfg.restaurant_name,
        "DiaChi": cfg.address,
        "MauHoaDon": cfg.invoice_template,
        "NguongTonMacDinh": float(cfg.default_stock_threshold),
        "SoNgayCanhBaoHetHan": cfg.expiry_warning_days,
        "ThoiGianGiuChoPhut": cfg.hold_minutes,
        "SoCauHoiAIMoiNgay": cfg.ai_daily_question_quota,
    }
    # Only allow documented configuration fields.
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
    if "SoNgayCanhBaoHetHan" in d and d["SoNgayCanhBaoHetHan"] is not None:
        cfg.expiry_warning_days = int(d["SoNgayCanhBaoHetHan"])
    if "ThoiGianGiuChoPhut" in d and d["ThoiGianGiuChoPhut"] is not None:
        cfg.hold_minutes = int(d["ThoiGianGiuChoPhut"])
    if "SoCauHoiAIMoiNgay" in d and d["SoCauHoiAIMoiNgay"] is not None:
        cfg.ai_daily_question_quota = int(d["SoCauHoiAIMoiNgay"])
    requested_start = d.get("GioBatDauBusinessDate")
    if requested_start is not None:
        with business_date.business_date_schedule(before_schedule):
            current_day = business_date.business_date_of(business_date.now())
            effective_day = current_day + timedelta(days=1)
            active_cutoff = business_date.cutoff_for(current_day)
            next_boundary = business_date.business_date_start(effective_day)
        pending = await session.get(BusinessDateCutoff, effective_day)
        previous = tuple(c for c in before_schedule if c.effective_date < effective_day)
        with business_date.business_date_schedule(previous):
            original_boundary = business_date.business_date_start(effective_day)
        moment = business_date.now()
        local_now = (
            moment.astimezone(business_date.VN_TZ).replace(tzinfo=None) if moment.tzinfo else moment
        )
        if requested_start == active_cutoff and original_boundary > local_now:
            if pending is not None:
                await session.delete(pending)
        elif requested_start != active_cutoff or pending is not None:
            # A later pending boundary may already be keeping the current day open.
            # Retain it when editing so no interval is reclassified retroactively.
            starts_at = max(next_boundary, datetime.combine(effective_day, requested_start))
            if pending is None:
                session.add(
                    BusinessDateCutoff(
                        effective_date=effective_day,
                        start_time=requested_start,
                        starts_at=starts_at,
                    )
                )
            else:
                pending.start_time, pending.starts_at = requested_start, starts_at
    before["LichGioBusinessDate"] = [
        {
            "NgayHieuLuc": c.effective_date.isoformat(),
            "GioBatDau": c.start_time.isoformat(),
            "ThoiDiemBatDau": c.starts_at.isoformat() if c.starts_at else None,
        }
        for c in before_schedule
    ]
    await session.flush()
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="UPDATE_CONFIG",
            target_entity="CAU_HINH_HE_THONG",
            target_id=str(cfg.id),
            before=before,
            after={
                "GioBatDauBusinessDateYeuCau": requested_start.isoformat()
                if requested_start
                else None,
                "TenNhaHang": cfg.restaurant_name,
                "DiaChi": cfg.address,
                "MauHoaDon": cfg.invoice_template,
                "NguongTonMacDinh": float(cfg.default_stock_threshold),
                "SoNgayCanhBaoHetHan": cfg.expiry_warning_days,
                "ThoiGianGiuChoPhut": cfg.hold_minutes,
                "SoCauHoiAIMoiNgay": cfg.ai_daily_question_quota,
            },
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
    target: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
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
    if target:
        q = q.where(SystemAuditLog.target_entity == target)
        cq = cq.where(SystemAuditLog.target_entity == target)
    if date_from:
        start = datetime.combine(date_from, time.min)
        q = q.where(SystemAuditLog.occurred_at >= start)
        cq = cq.where(SystemAuditLog.occurred_at >= start)
    if date_to:
        end = datetime.combine(date_to, time.min) + timedelta(days=1)
        q = q.where(SystemAuditLog.occurred_at < end)
        cq = cq.where(SystemAuditLog.occurred_at < end)
    total = (await session.execute(cq)).scalar_one()
    result = await session.execute(
        q.order_by(SystemAuditLog.id.desc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total


async def list_audit_actions(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(SystemAuditLog.action).distinct().order_by(SystemAuditLog.action)
    )
    return list(result.scalars().all())


REDACTED_BACKUP_COLUMNS = {"NGUOI_DUNG": {"MatKhauHash"}}


async def export_backup(
    session: AsyncSession, actor_id: int, *, include_credentials: bool = False
) -> dict:
    """Dump every table and audit the export in the same transaction (NFR-10).

    Rows use the physical Vietnamese column names so they can be restored table by
    table. Password hashes stay out by default; a manager may request them with
    `include_credentials` when the export itself is protected (file encryption,
    restricted storage), otherwise accounts must be re-secured after a restore.
    """
    now = datetime.now(UTC)
    redactions = {} if include_credentials else REDACTED_BACKUP_COLUMNS
    data: dict[str, list[dict]] = {}
    for table in Base.metadata.sorted_tables:
        rows = (await session.execute(select(table))).mappings().all()
        redacted = redactions.get(table.name, set())
        data[table.name] = [
            {key: value for key, value in dict(row).items() if key not in redacted} for row in rows
        ]
    session.add(
        SystemAuditLog(
            user_id=actor_id,
            action="EXPORT_BACKUP",
            target_entity="SYSTEM",
            target_id="backup",
            after={"BaoGomThongTinXacThuc": include_credentials},
        )
    )
    await session.flush()
    return {
        "created_at": now,
        "covers_until": now,
        "tables": list(data),
        "credentials_included": include_credentials,
        "redacted_columns": [
            f"{table}.{column}"
            for table, columns in sorted(redactions.items())
            for column in sorted(columns)
        ],
        "restore_notes": [
            "Tắt ứng dụng, khôi phục theo đúng thứ tự trong 'tables' (bảng cha trước).",
            "Bật lại ứng dụng và đăng nhập bằng tài khoản quản lý đã có trong bản sao.",
            "Nếu credentials_included=false: dùng chức năng đặt lại mật khẩu cho từng "
            "tài khoản, hoặc tạo tài khoản quản lý mới bằng công cụ CSDL.",
            "Bản sao có mật khẩu băm vẫn là dữ liệu nhạy cảm: mã hoá file và huỷ sau khi dùng.",
        ],
        "data": data,
    }


async def config_output(session: AsyncSession, cfg: SystemConfig) -> dict:
    """Expose the active cutoff and the pending transition without mutating history."""
    from app.modules.settings.schemas import ConfigOut

    changes = await business_date.load_business_date_schedule(session)
    with business_date.business_date_schedule(changes):
        current = business_date.business_date_of(business_date.now())
        result = ConfigOut.model_validate(cfg).model_dump()
        result["GioBatDauBusinessDate"] = business_date.cutoff_for(current)
        pending = next((c for c in changes if c.effective_date > current), None)
        if pending is not None:
            result.update(
                GioBatDauBusinessDateMoi=pending.start_time,
                NgayHieuLucGioMoi=pending.effective_date,
                ThoiDiemApDungGioMoi=pending.starts_at,
            )
        return result
