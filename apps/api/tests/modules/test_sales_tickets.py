"""Task 3 tickets."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import (
    DiningTable,
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
)
from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.enums import VersionStatus
from tests.helpers import ticket_by_id, tickets_for


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="CASHIER", username="tester"):
    await seed_reference_data(session)
    from sqlalchemy import select as sel

    r = await session.execute(sel(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}, u


async def _setup(session):
    g = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    d = Dish(name="Món", group_id=g.id, is_deleted=False)
    session.add(d)
    await session.flush()
    ing = Ingredient(name="NL", unit="kg", min_stock=1, stock_qty=20, is_deleted=False)
    session.add(ing)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    pv = DishPriceVersion(
        dish_id=d.id,
        price=50000,
        business_date=bd,
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    session.add(pv)
    await session.flush()
    rc = Recipe(
        dish_id=d.id, business_date=bd, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới"
    )
    session.add(rc)
    await session.flush()
    session.add(RecipeItem(recipe_id=rc.id, ingredient_id=ing.id, quantity=1))
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=20, unit_price=1000)
    session.add(gl)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        receipt_line_id=gl.id,
        quantity_remaining=20,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    t = DiningTable(name="Bàn 1", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return d, t


@pytest.mark.anyio
async def test_ticket_carries_info(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 2, "GhiChu": "không hành"}]},
        headers=h,
    )
    assert r.status_code == 201
    oid = r.json()["MaOrder"]
    tickets = await tickets_for(session, oid)
    assert len(tickets) == 1
    assert r.json()["MaOrderHienThi"] in tickets[0]["NoiDung"]
    assert "không hành" in tickets[0]["NoiDung"]
    assert "2" in tickets[0]["NoiDung"]


@pytest.mark.anyio
async def test_adding_dish_prints_additional_ticket(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )
    oid = r.json()["MaOrder"]
    # add another line
    r2 = await client.post(
        f"/api/v1/sales/orders/{oid}/lines", json={"dish_id": d.id, "quantity": 1}, headers=h
    )
    assert r2.status_code == 201
    tickets = await tickets_for(session, oid)
    assert len(tickets) == 2


@pytest.mark.anyio
async def test_reprint_unlimited(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )
    oid = r.json()["MaOrder"]
    tickets = await tickets_for(session, oid)
    tid = tickets[0]["MaPhieuBep"]

    # reprint 3 times
    for _ in range(3):
        rr = await client.post(f"/api/v1/sales/orders/{oid}/tickets/{tid}/reprint", headers=h)
        assert rr.status_code == 200
    row = await ticket_by_id(session, tid)
    assert row["SoLanIn"] == 4


@pytest.mark.anyio
async def test_warehouse_cannot_reprint(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session, role="CASHIER", username="cash")
    h2, _ = await _headers(session, role="WAREHOUSE", username="kho")
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )
    oid = r.json()["MaOrder"]
    tickets = await tickets_for(session, oid)
    tid = tickets[0]["MaPhieuBep"]
    rr = await client.post(f"/api/v1/sales/orders/{oid}/tickets/{tid}/reprint", headers=h2)
    assert rr.status_code == 403
