"""FR-SET-01, FR-SET-04, FR-SET-08/09: accounts, ranges and audit before/after."""

import pytest
from sqlalchemy import select

from app.core.errors import BusinessRuleError
from app.core.security import create_access_token, hash_password
from app.modules.settings import service as svc
from app.modules.settings.models import SystemConfig, User
from app.modules.settings.schemas import UserUpdate
from app.modules.settings.service import seed_reference_data
from app.shared.audit import SystemAuditLog

USERS = "/api/v1/settings/users"
CONFIG = "/api/v1/settings/config"


async def _account(session, username: str, role: str, status: str = "Hoạt động") -> User:
    await seed_reference_data(session)
    user = User(
        username=username,
        password_hash=hash_password("pass123"),
        full_name=username,
        role_id=role,
        status=status,
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


def _auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}


# --- accounts -------------------------------------------------------------------------------


async def test_a_manager_edits_the_profile_and_role_with_before_and_after_in_the_log(
    api_client, session
):
    manager = await _account(session, "ql01", "MANAGER")
    cashier = await _account(session, "tn01", "CASHIER")
    async with api_client as client:
        response = await client.patch(
            f"{USERS}/{cashier.id}",
            json={"full_name": "Thu Ngân Mới", "phone": "0901", "role": "WAREHOUSE"},
            headers=_auth(manager),
        )

    assert response.status_code == 200, response.text
    assert response.json()["MaVaiTro"] == "WAREHOUSE"
    entry = (
        await session.execute(select(SystemAuditLog).where(SystemAuditLog.action == "UPDATE_USER"))
    ).scalar_one()
    assert entry.user_id == manager.id
    assert entry.before == {"HoTen": "tn01", "SoDienThoai": None, "MaVaiTro": "CASHIER"}
    assert entry.after == {"HoTen": "Thu Ngân Mới", "SoDienThoai": "0901", "MaVaiTro": "WAREHOUSE"}
    assert "MatKhauHash" not in str(entry.after)


async def test_only_a_manager_may_edit_accounts(api_client, session):
    cashier = await _account(session, "tn01", "CASHIER")
    warehouse = await _account(session, "kho01", "WAREHOUSE")
    async with api_client as client:
        response = await client.patch(
            f"{USERS}/{warehouse.id}", json={"full_name": "x"}, headers=_auth(cashier)
        )

    assert response.status_code == 403


async def test_an_unknown_role_or_field_is_rejected(api_client, session):
    manager = await _account(session, "ql01", "MANAGER")
    cashier = await _account(session, "tn01", "CASHIER")
    async with api_client as client:
        unknown_role = await client.patch(
            f"{USERS}/{cashier.id}", json={"role": "BEP"}, headers=_auth(manager)
        )
        smuggled = await client.patch(
            f"{USERS}/{cashier.id}", json={"status": "Đã khóa"}, headers=_auth(manager)
        )
        missing = await client.patch(
            f"{USERS}/9999", json={"full_name": "x"}, headers=_auth(manager)
        )

    assert unknown_role.status_code == 422
    assert smuggled.status_code == 422
    assert missing.status_code == 404


async def test_a_manager_cannot_change_their_own_role(api_client, session):
    manager = await _account(session, "ql01", "MANAGER")
    await _account(session, "ql02", "MANAGER")
    async with api_client as client:
        response = await client.patch(
            f"{USERS}/{manager.id}", json={"role": "CASHIER"}, headers=_auth(manager)
        )

    assert response.status_code == 422
    await session.refresh(manager)
    assert manager.role_id == "MANAGER"


async def test_the_last_active_manager_cannot_be_demoted_or_locked(session):
    sole = await _account(session, "ql01", "MANAGER")

    with pytest.raises(BusinessRuleError, match="cuối cùng"):
        await svc.update_user(session, None, sole.id, UserUpdate(role="CASHIER"))
    with pytest.raises(BusinessRuleError, match="cuối cùng"):
        await svc.lock_user(session, 9999, sole.id)
    assert sole.role_id == "MANAGER"
    assert sole.status == "Hoạt động"

    # A second active manager lifts the restriction; a locked one does not count.
    second = await _account(session, "ql02", "MANAGER", status="Đã khóa")
    with pytest.raises(BusinessRuleError, match="cuối cùng"):
        await svc.update_user(session, second.id, sole.id, UserUpdate(role="CASHIER"))
    await svc.unlock_user(session, sole.id, second.id)
    demoted = await svc.update_user(session, second.id, sole.id, UserUpdate(role="CASHIER"))
    assert demoted.role_id == "CASHIER"


async def test_a_locked_account_is_also_refused_by_the_edit_endpoint_caller(api_client, session):
    manager = await _account(session, "ql01", "MANAGER", status="Đã khóa")
    cashier = await _account(session, "tn01", "CASHIER")
    async with api_client as client:
        response = await client.patch(
            f"{USERS}/{cashier.id}", json={"full_name": "x"}, headers=_auth(manager)
        )

    assert response.status_code == 401


# --- configuration (FR-SET-04) ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("SoNgayCanhBaoHetHan", 0),
        ("SoNgayCanhBaoHetHan", 366),
        ("SoCauHoiAIMoiNgay", 0),
        ("SoCauHoiAIMoiNgay", -5),
        ("SoCauHoiAIMoiNgay", 10_001),
        ("ThoiGianGiuChoPhut", 0),
        ("ThoiGianGiuChoPhut", 1_441),
        ("NguongTonMacDinh", -1),
        ("NguongTonMacDinh", 1_000_001),
    ],
)
async def test_out_of_range_settings_are_rejected(api_client, session, field, value):
    manager = await _account(session, "ql01", "MANAGER")
    async with api_client as client:
        response = await client.put(CONFIG, json={field: value}, headers=_auth(manager))

    assert response.status_code == 422, response.text
    config = (await session.execute(select(SystemConfig))).scalar_one()
    assert config.ai_daily_question_quota == 50


async def test_boundary_settings_are_accepted_and_zero_is_a_valid_threshold(api_client, session):
    manager = await _account(session, "ql01", "MANAGER")
    async with api_client as client:
        response = await client.put(
            CONFIG,
            json={
                "SoNgayCanhBaoHetHan": 365,
                "SoCauHoiAIMoiNgay": 1,
                "ThoiGianGiuChoPhut": 1_440,
                "NguongTonMacDinh": 0,
            },
            headers=_auth(manager),
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["SoNgayCanhBaoHetHan"], body["SoCauHoiAIMoiNgay"]) == (365, 1)
    assert (body["ThoiGianGiuChoPhut"], body["NguongTonMacDinh"]) == (1_440, 0)


async def test_a_fractional_default_threshold_is_kept(api_client, session):
    manager = await _account(session, "ql01", "MANAGER")
    async with api_client as client:
        response = await client.put(CONFIG, json={"NguongTonMacDinh": 2.5}, headers=_auth(manager))

    assert response.status_code == 200
    assert response.json()["NguongTonMacDinh"] == 2.5


async def test_the_config_change_is_audited_with_before_and_after(api_client, session):
    manager = await _account(session, "ql01", "MANAGER")
    async with api_client as client:
        await client.put(CONFIG, json={"SoCauHoiAIMoiNgay": 7}, headers=_auth(manager))

    entry = (
        await session.execute(
            select(SystemAuditLog).where(SystemAuditLog.action == "UPDATE_CONFIG")
        )
    ).scalar_one()
    assert entry.before["SoCauHoiAIMoiNgay"] == 50
    assert entry.after["SoCauHoiAIMoiNgay"] == 7
