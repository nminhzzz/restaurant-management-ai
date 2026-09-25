"""Account locking and manual backup: FR-SET-01, FR-SET-06, FR-SET-08."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.errors import BusinessRuleError
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings import service as svc
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared.audit import SystemAuditLog
from app.shared.roles import Role

ACTIVE = "Hoạt động"
LOCKED = "Đã khóa"


async def _staff(session) -> tuple[User, User]:
    await seed_reference_data(session)
    manager = User(
        username="quanly01",
        password_hash=hash_password("pass123"),
        full_name="Lê Thảo",
        role_id=Role.MANAGER.value,
        status=ACTIVE,
    )
    cashier = User(
        username="thungan01",
        password_hash=hash_password("pass123"),
        full_name="Phạm Thu Hà",
        role_id=Role.CASHIER.value,
        status=ACTIVE,
    )
    session.add_all([manager, cashier])
    await session.flush()
    return manager, cashier


def _client(session) -> AsyncClient:
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _bearer(user: User) -> dict[str, str]:
    token = create_access_token(str(user.id), {"role": user.role_id, "username": user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_a_locked_account_can_be_unlocked_and_both_steps_are_audited(session):
    manager, cashier = await _staff(session)

    await svc.lock_user(session, manager.id, cashier.id)
    unlocked = await svc.unlock_user(session, manager.id, cashier.id)

    assert unlocked.status == ACTIVE
    actions = (
        (
            await session.execute(
                select(SystemAuditLog.action).where(SystemAuditLog.target_id == str(cashier.id))
            )
        )
        .scalars()
        .all()
    )
    assert actions == ["LOCK_USER", "UNLOCK_USER"]


@pytest.mark.asyncio
async def test_a_manager_cannot_lock_their_own_account(session):
    manager, _ = await _staff(session)

    with pytest.raises(BusinessRuleError):
        await svc.lock_user(session, manager.id, manager.id)
    assert manager.status == ACTIVE


@pytest.mark.asyncio
async def test_the_unlock_endpoint_is_manager_only(session):
    manager, cashier = await _staff(session)
    await svc.lock_user(session, manager.id, cashier.id)
    await session.commit()

    async with _client(session) as client:
        forbidden = await client.patch(
            f"/api/v1/settings/users/{cashier.id}/unlock", headers=_bearer(cashier)
        )
        allowed = await client.patch(
            f"/api/v1/settings/users/{cashier.id}/unlock", headers=_bearer(manager)
        )
    app.dependency_overrides.clear()

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["TrangThai"] == ACTIVE


@pytest.mark.asyncio
async def test_the_backup_contains_the_data_of_every_table_and_is_audited(session):
    manager, _ = await _staff(session)
    await session.commit()

    async with _client(session) as client:
        response = await client.post("/api/v1/settings/backup", headers=_bearer(manager))
    app.dependency_overrides.clear()

    assert response.status_code == 200
    dump = response.json()
    assert "NGUOI_DUNG" in dump["tables"]
    assert set(dump["tables"]) == set(dump["data"])
    usernames = {row["TenDangNhap"] for row in dump["data"]["NGUOI_DUNG"]}
    assert usernames == {"quanly01", "thungan01"}
    audited = (
        await session.execute(
            select(SystemAuditLog).where(SystemAuditLog.action == "EXPORT_BACKUP")
        )
    ).scalar_one()
    assert audited.user_id == manager.id
