import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import latest_audit


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers_for(session, role="MANAGER"):
    await seed_reference_data(session)
    username = "quanly01" if role == "MANAGER" else "kho01"
    r = await session.execute(select(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass123"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    return {
        "Authorization": f"Bearer {create_access_token(str(u.id), {'role': u.role_id, 'username': u.username})}"
    }


async def update_supplier(client, headers, sid, **kw):
    body = {}
    if "name" in kw:
        body["TenNhaCungCap"] = kw.pop("name")
    if "phone" in kw:
        body["SoDienThoai"] = kw.pop("phone")
    body.update(kw)
    return await client.patch(f"/api/v1/catalog/suppliers/{sid}", json=body, headers=headers)


async def get_supplier_row(session, sid):
    from app.modules.catalog.models import Supplier

    return await session.get(Supplier, sid)


@pytest.mark.asyncio
async def test_a_manager_can_update_a_suppliers_name_and_phone(session, fresh_supplier):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        resp = await update_supplier(c, h, fresh_supplier.id, name="NCC B", phone="0909000111")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert body["TenNhaCungCap"] == "NCC B"
    assert body["SoDienThoai"] == "0909000111"
    row = await get_supplier_row(session, fresh_supplier.id)
    assert row.name == "NCC B"
    assert row.phone == "0909000111"


@pytest.mark.asyncio
async def test_warehouse_staff_can_update_a_supplier(session, fresh_supplier):
    h = await _headers_for(session, "WAREHOUSE")
    async with await _make_client(session) as c:
        resp = await update_supplier(c, h, fresh_supplier.id, phone="0912345678")
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    assert resp.json()["SoDienThoai"] == "0912345678"


@pytest.mark.asyncio
async def test_updating_a_supplier_is_audited(session, fresh_supplier):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        await update_supplier(c, h, fresh_supplier.id, name="NCC C")
    app.dependency_overrides.clear()
    assert (await latest_audit(session))["LoaiThaoTac"] == "UPDATE_SUPPLIER"


@pytest.mark.asyncio
async def test_updating_a_missing_supplier_is_rejected(session):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        resp = await update_supplier(c, h, 999999, name="X")
    app.dependency_overrides.clear()
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_the_cashier_cannot_update_a_supplier(session, fresh_supplier):
    await seed_reference_data(session)
    r = await session.execute(select(User).where(User.username == "thungan01"))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username="thungan01",
            password_hash=hash_password("pass123"),
            full_name="Thu ngân",
            role_id="CASHIER",
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    h = {
        "Authorization": f"Bearer {create_access_token(str(u.id), {'role': u.role_id, 'username': u.username})}"
    }
    async with await _make_client(session) as c:
        resp = await update_supplier(c, h, fresh_supplier.id, name="NCC D")
    app.dependency_overrides.clear()
    assert resp.status_code == 403
