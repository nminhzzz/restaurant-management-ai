"""Phase 4 Task 2 — line status, cancel, move, cancel order."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.enums import VersionStatus
from app.modules.catalog.models import Dish, DishGroup, Ingredient, Recipe, RecipeItem, DishPriceVersion, DiningTable
from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot
from tests.helpers import ingredient_total, table_status, order_status, line_status


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
        u = User(username=username, password_hash=hash_password("pass"), full_name=username, role_id=role, status="Hoạt động")
        session.add(u); await session.flush(); await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}, u


async def _setup_dish_with_stock(session, qty=10, need=1, dish_name="Món"):
    g = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(g); await session.flush()
    d = Dish(name=dish_name, group_id=g.id, is_deleted=False)
    session.add(d); await session.flush()
    ing = Ingredient(name="NL_"+dish_name, unit="kg", min_stock=1, stock_qty=qty, is_deleted=False)
    session.add(ing); await session.flush()
    bd = business_date.business_date_of(business_date.now())
    pv = DishPriceVersion(dish_id=d.id, price=50000, business_date=bd, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới")
    session.add(pv); await session.flush()
    rc = Recipe(dish_id=d.id, business_date=bd, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới")
    session.add(rc); await session.flush()
    session.add(RecipeItem(recipe_id=rc.id, ingredient_id=ing.id, quantity=need))
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr); await session.flush()
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=qty, unit_price=1000)
    session.add(gl); await session.flush()
    lot = IngredientLot(ingredient_id=ing.id, receipt_line_id=gl.id, quantity_remaining=qty, status="Còn hạn", received_at=business_date.now())
    session.add(lot); await session.flush(); await session.commit()
    return d, ing


async def _table(session, name="Bàn 1"):
    t = DiningTable(name=name, is_deleted=False, status="Trống")
    session.add(t); await session.flush(); await session.commit()
    return t


async def _submit(session, client, headers, dish, table):
    r = await client.post("/api/v1/sales/orders", json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]}, headers=headers)
    assert r.status_code == 201, r.text
    j = r.json()
    return j["MaOrder"], j["lines"][0]["MaChiTietOrder"]


@pytest.mark.anyio
async def test_status_only_moves_forward(session):
    d, ing = await _setup_dish_with_stock(session)
    t = await _table(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, lid = await _submit(session, client, h, d, t)
    r = await client.patch(f"/api/v1/sales/orders/{oid}/lines/{lid}/status", json={"to": "Đã xác nhận xong"}, headers=h)
    assert r.status_code == 200
    r = await client.patch(f"/api/v1/sales/orders/{oid}/lines/{lid}/status", json={"to": "Đã phục vụ"}, headers=h)
    assert r.status_code == 200
    assert await line_status(session, lid) == "Đã phục vụ"
    r = await client.patch(f"/api/v1/sales/orders/{oid}/lines/{lid}/status", json={"to": "Chờ"}, headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_waiting_line_cancel_returns_stock(session):
    d, ing = await _setup_dish_with_stock(session, qty=10)
    t = await _table(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, lid = await _submit(session, client, h, d, t)
    before = await ingredient_total(session, d)
    r = await client.post(f"/api/v1/sales/orders/{oid}/lines/{lid}/cancel", json={"reason": "khách đổi ý"}, headers=h)
    assert r.status_code == 200
    after = await ingredient_total(session, d)
    assert after == before + 1


@pytest.mark.anyio
async def test_confirmed_line_cannot_cancel(session):
    d, ing = await _setup_dish_with_stock(session)
    t = await _table(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, lid = await _submit(session, client, h, d, t)
    await client.patch(f"/api/v1/sales/orders/{oid}/lines/{lid}/status", json={"to": "Đã xác nhận xong"}, headers=h)
    r = await client.post(f"/api/v1/sales/orders/{oid}/lines/{lid}/cancel", json={"reason": "x"}, headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_move_table(session):
    d, ing = await _setup_dish_with_stock(session)
    t = await _table(session, "Bàn A")
    t2 = await _table(session, "Bàn B")
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, _ = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/move", json={"MaBanDich": t2.id}, headers=h)
    assert r.status_code == 200
    assert r.json()["MaBan"] == t2.id
    assert await table_status(session, t.id) == "Trống"
    assert await table_status(session, t2.id) == "Đang phục vụ"


@pytest.mark.anyio
async def test_move_to_occupied_refused(session):
    d, ing = await _setup_dish_with_stock(session)
    t = await _table(session, "A")
    t2 = DiningTable(name="B", is_deleted=False, status="Đang phục vụ")
    session.add(t2); await session.flush(); await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, _ = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/move", json={"MaBanDich": t2.id}, headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_only_manager_cancel_whole(session):
    d, ing = await _setup_dish_with_stock(session)
    t = await _table(session)
    client = await _make_client(session)
    h_cash, _ = await _headers(session, role="CASHIER", username="cashier01")
    h_mgr, _ = await _headers(session, role="MANAGER", username="manager01")
    oid, _ = await _submit(session, client, h_cash, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/cancel", json={"reason": "x"}, headers=h_cash)
    assert r.status_code == 403
    r = await client.post(f"/api/v1/sales/orders/{oid}/cancel", json={"reason": "khách bỏ về"}, headers=h_mgr)
    assert r.status_code == 200
    assert await order_status(session, oid) == "Đã hủy"


@pytest.mark.anyio
async def test_cancel_whole_requires_reason(session):
    d, ing = await _setup_dish_with_stock(session)
    t = await _table(session)
    client = await _make_client(session)
    h, _ = await _headers(session, role="MANAGER", username="mgr2")
    oid, _ = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/cancel", json={"reason": ""}, headers=h)
    assert r.status_code == 422
