from datetime import timedelta

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


async def _submit(session, client, h, d, t):
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )
    assert r.status_code == 201
    return r.json()["MaOrder"], r.json()["lines"][0]["MaChiTietOrder"]


@pytest.mark.anyio
async def test_settled_rejects_mutation(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    hm, _ = await _headers(session, role="MANAGER", username="mgr")
    oid, lid = await _submit(session, client, h, d, t)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    r = await client.post(
        f"/api/v1/sales/orders/{oid}/lines", json={"dish_id": d.id, "quantity": 1}, headers=h
    )
    assert r.status_code == 422
    r = await client.post(
        f"/api/v1/sales/orders/{oid}/lines/{lid}/cancel", json={"reason": "x"}, headers=h
    )
    assert r.status_code == 422
    r = await client.post(f"/api/v1/sales/orders/{oid}/cancel", json={"reason": "x"}, headers=hm)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_reprint_invoice(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, _ = await _submit(session, client, h, d, t)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    r = await client.get(f"/api/v1/sales/orders/{oid}/invoice", headers=h)
    assert r.status_code == 200
    r2 = await client.post(f"/api/v1/sales/orders/{oid}/invoice/reprint", headers=h)
    assert r2.json()["SoHoaDon"] == r.json()["SoHoaDon"]


@pytest.mark.anyio
async def test_invoice_carries_printable_detail(session):
    """FR-SALE-19/23: enough for a printable receipt (restaurant, lines, method, time)."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, _ = await _submit(session, client, h, d, t)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)

    r = await client.get(f"/api/v1/sales/orders/{oid}/invoice", headers=h)
    body = r.json()
    assert body["TenNhaHang"]
    assert body["PhuongThucThanhToan"] == "Tiền mặt"
    assert body["ThoiDiemXuat"]
    assert len(body["lines"]) == 1
    assert body["lines"][0]["TenMon"] == "Món"
    assert body["lines"][0]["SoLuong"] == 1


@pytest.mark.anyio
async def test_search_orders(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, _ = await _submit(session, client, h, d, t)
    from app.modules.sales.models import Order

    o = await session.get(Order, oid)
    r = await client.get(f"/api/v1/sales/orders?code={o.display_code}", headers=h)
    assert r.json()["total"] == 1


@pytest.mark.anyio
async def test_search_lists_newest_first_and_filters_by_status_and_table(session):
    """FR-SALE-22: look an order up by table and Business Date, not only by code."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    first, _ = await _submit(session, client, h, d, t)
    await client.post(f"/api/v1/sales/orders/{first}/pay/cash", headers=h)
    second, _ = await _submit(session, client, h, d, t)
    today = business_date.business_date_of(business_date.now()).isoformat()

    everything = await client.get(
        f"/api/v1/sales/orders?table_id={t.id}&business_date={today}", headers=h
    )
    open_only = await client.get("/api/v1/sales/orders?status=Đang mở", headers=h)

    assert [o["MaOrder"] for o in everything.json()["items"]] == [second, first]
    assert [o["MaOrder"] for o in open_only.json()["items"]] == [second]


@pytest.mark.anyio
async def test_search_caps_the_number_of_rows(session):
    """A search with no filter must not ship a year of orders to the browser."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    for _ in range(3):
        oid, _ = await _submit(session, client, h, d, t)
        await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)

    r = await client.get("/api/v1/sales/orders?limit=2", headers=h)

    assert len(r.json()["items"]) == 2


@pytest.mark.anyio
async def test_search_paginates_and_reports_a_real_total(session):
    """`total` must reflect every matching row, not just the rows on the current page."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    for _ in range(5):
        oid, _ = await _submit(session, client, h, d, t)
        await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)

    page1 = await client.get("/api/v1/sales/orders?page=1&size=2", headers=h)
    page2 = await client.get("/api/v1/sales/orders?page=2&size=2", headers=h)

    assert page1.json()["total"] == 5
    assert page2.json()["total"] == 5
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 2
    assert page1.json()["items"] != page2.json()["items"]


@pytest.mark.anyio
async def test_search_filters_by_business_date_range(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid, _ = await _submit(session, client, h, d, t)
    today = business_date.business_date_of(business_date.now())
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    in_range = await client.get(
        f"/api/v1/sales/orders?date_from={yesterday.isoformat()}&date_to={today.isoformat()}",
        headers=h,
    )
    out_of_range = await client.get(
        f"/api/v1/sales/orders?date_from={tomorrow.isoformat()}&date_to={tomorrow.isoformat()}",
        headers=h,
    )

    assert oid in [o["MaOrder"] for o in in_range.json()["items"]]
    assert oid not in [o["MaOrder"] for o in out_of_range.json()["items"]]


@pytest.mark.anyio
async def test_search_rejects_a_malformed_business_date(session):
    """Silently dropping a bad date filter would return every order instead of none."""
    await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)

    r = await client.get("/api/v1/sales/orders?business_date=25-09-2026", headers=h)

    assert r.status_code == 422
