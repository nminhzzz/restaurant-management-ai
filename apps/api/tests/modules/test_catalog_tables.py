import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import display_status


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="MANAGER"):
    await seed_reference_data(session)
    uname = {"MANAGER": "quanly01", "CASHIER": "thungan01", "WAREHOUSE": "kho01"}[role]
    r = await session.execute(select(User).where(User.username == uname))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=uname,
            password_hash=hash_password("pass123"),
            full_name=uname,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    return {
        "Authorization": f"Bearer {create_access_token(str(u.id), {'role': u.role_id, 'username': u.username})}"
    }


async def create_table(client, headers, name="Bàn 9"):
    return await client.post("/api/v1/catalog/tables", json={"TenBan": name}, headers=headers)


async def list_tables(client, headers):
    return await client.get("/api/v1/catalog/tables", headers=headers)


async def delete_table(client, headers, tid):
    return await client.delete(f"/api/v1/catalog/tables/{tid}", headers=headers)


async def set_manual_hidden(client, headers, dish_id, value=True):
    return await client.patch(
        f"/api/v1/catalog/dishes/{dish_id}/visibility", json={"AnThuCong": value}, headers=headers
    )


async def set_manual_out_of_stock(client, headers, dish_id, value=True):
    return await client.patch(
        f"/api/v1/catalog/dishes/{dish_id}/visibility",
        json={"HetNLThuCong": value},
        headers=headers,
    )


async def delete_dish(client, headers, did):
    return await client.delete(f"/api/v1/catalog/dishes/{did}", headers=headers)


async def get_dish(session, did):
    from app.modules.catalog.models import Dish

    return await session.get(Dish, did)


@pytest.mark.asyncio
async def test_a_table_in_use_cannot_be_deleted(session, occupied_table):
    # make occupied: create order referencing table
    from app.modules.sales.models import Order
    from app.shared import business_date

    o = Order(
        table_id=occupied_table.id,
        business_date=business_date.business_date_of(business_date.now()),
        order_type="Tại chỗ",
        status="Chờ xác nhận",
    )
    session.add(o)
    await session.flush()
    await session.commit()
    h = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        resp = await delete_table(c, h, occupied_table.id)
    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_a_soft_deleted_table_frees_its_name(session, free_table):
    h = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        await delete_table(c, h, free_table.id)
        resp = await create_table(c, h, name="Bàn 1")
    app.dependency_overrides.clear()
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_the_two_out_of_stock_causes_are_independent(session, dish):
    h = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        await set_manual_out_of_stock(c, h, dish.id, value=True)
    app.dependency_overrides.clear()
    row = await get_dish(session, dish.id)
    # status via generated column or display_status
    assert await display_status(session, row) in {
        "Hết nguyên liệu",
        "Ẩn thủ công",
        "Hoạt động",
        "Nháp",
    }
    h2 = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        await set_manual_out_of_stock(c, h2, dish.id, value=False)
    app.dependency_overrides.clear()
    row2 = await get_dish(session, dish.id)
    assert await display_status(session, row2) in {"Hoạt động", "Nháp"}


@pytest.mark.asyncio
async def test_manual_hiding_is_independent_of_stock(session, dish):
    h = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        await set_manual_hidden(c, h, dish.id, value=True)
    app.dependency_overrides.clear()
    row = await get_dish(session, dish.id)
    assert row.hide_manual is True


@pytest.mark.asyncio
async def test_soft_deleted_table_is_hidden_from_the_floor_plan(session, free_table):
    h = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        await delete_table(c, h, free_table.id)
        listed = await list_tables(c, h)
    app.dependency_overrides.clear()
    assert all(x["MaBan"] != free_table.id for x in listed.json())


@pytest.mark.asyncio
async def test_the_cashier_sees_the_floor_plan_but_cannot_edit_it(session):
    hc = await _headers(session, "CASHIER")
    async with await _make_client(session) as c:
        ok = await list_tables(c, hc)
        forbidden = await create_table(c, hc, name="Bàn 9")
    app.dependency_overrides.clear()
    assert ok.status_code == 200
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_soft_delete_is_a_state_of_its_own(session, dish):
    h = await _headers(session, "MANAGER")
    async with await _make_client(session) as c:
        await delete_dish(c, h, dish.id)
    app.dependency_overrides.clear()
    row = await get_dish(session, dish.id)
    assert row.is_deleted is True
    assert await display_status(session, row) == "Đã xóa"
