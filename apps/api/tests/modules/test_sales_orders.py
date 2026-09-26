"""Phase 4 Task 1 — submit, code, stock."""

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
from tests.helpers import ingredient_total, order_count


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _cashier_headers(session):
    await seed_reference_data(session)
    # ensure cashier exists
    from sqlalchemy import select as sel

    r = await session.execute(sel(User).where(User.username == "cashier01"))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username="cashier01",
            password_hash=hash_password("pass"),
            full_name="Cashier",
            role_id="CASHIER",
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}


async def _setup_dish_with_stock(
    session, stock_qty=10, dish_name="Món A", price=50000, need_per_unit=1
):
    # group
    g = DishGroup(name="Nhóm A", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    d = Dish(name=dish_name, group_id=g.id, is_deleted=False)
    session.add(d)
    await session.flush()
    ing = Ingredient(
        name="NL_" + dish_name, unit="kg", min_stock=1, stock_qty=stock_qty, is_deleted=False
    )
    session.add(ing)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    pv = DishPriceVersion(
        dish_id=d.id,
        price=price,
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
    session.add(RecipeItem(recipe_id=rc.id, ingredient_id=ing.id, quantity=need_per_unit))
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(
        receipt_id=gr.id, ingredient_id=ing.id, quantity=stock_qty, unit_price=1000
    )
    session.add(gl)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        receipt_line_id=gl.id,
        quantity_remaining=stock_qty,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    await session.flush()
    await session.commit()
    return d, ing, g


async def _setup_table(session, name="Bàn 1"):
    t = DiningTable(name=name, is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest.mark.anyio
async def test_submit_takes_price_and_recipe(session):
    d, ing, g = await _setup_dish_with_stock(session)
    t = await _setup_table(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 2}]},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["lines"][0]["DonGia"] == 50000
    assert j["lines"][0]["MaPhienBanGia"] is not None
    assert j["lines"][0]["MaCongThuc"] is not None


@pytest.mark.anyio
async def test_display_code_counts(session):
    d, ing, g = await _setup_dish_with_stock(session, stock_qty=20)
    t = await _setup_table(session, "Bàn A")
    t2 = await _setup_table(session, "Bàn B")
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r1 = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=headers,
    )
    r2 = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t2.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=headers,
    )
    assert r1.json()["MaOrderHienThi"].endswith("-001")
    assert r2.json()["MaOrderHienThi"].endswith("-002")


@pytest.mark.anyio
async def test_takeaway_no_table(session):
    d, ing, g = await _setup_dish_with_stock(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"LoaiDon": "Mang về", "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=headers,
    )
    assert r.status_code == 201
    assert r.json()["MaBan"] is None


@pytest.mark.anyio
async def test_rejected_when_out_of_stock(session):
    d, ing, g = await _setup_dish_with_stock(session, stock_qty=1)
    # scarce dish with 1 stock, ordering 99 fails

    # create scarce
    ing2 = Ingredient(name="NL hiếm", unit="kg", min_stock=1, stock_qty=1, is_deleted=False)
    session.add(ing2)
    await session.flush()
    d2 = Dish(name="Món hiếm", group_id=g.id, is_deleted=False)
    session.add(d2)
    await session.flush()
    bd2 = business_date.business_date_of(business_date.now())
    pv2 = DishPriceVersion(
        dish_id=d2.id,
        price=10000,
        business_date=bd2,
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    session.add(pv2)
    await session.flush()
    rc2 = Recipe(
        dish_id=d2.id, business_date=bd2, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới"
    )
    session.add(rc2)
    await session.flush()
    session.add(RecipeItem(recipe_id=rc2.id, ingredient_id=ing2.id, quantity=1))
    gr2 = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr2)
    await session.flush()
    gl2 = GoodsReceiptLine(receipt_id=gr2.id, ingredient_id=ing2.id, quantity=1, unit_price=5000)
    session.add(gl2)
    await session.flush()
    lot2 = IngredientLot(
        ingredient_id=ing2.id,
        receipt_line_id=gl2.id,
        quantity_remaining=1,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot2)
    await session.flush()
    await session.commit()

    t = await _setup_table(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": t.id,
            "lines": [{"MaMon": d.id, "SoLuong": 1}, {"MaMon": d2.id, "SoLuong": 99}],
        },
        headers=headers,
    )
    assert r.status_code == 201
    assert [x["MaMon"] for x in r.json()["lines"]] == [d.id]
    assert r.json()["rejected"] == [{"MaMon": d2.id, "reason": "không đủ tồn kho"}]


@pytest.mark.anyio
async def test_all_fail_returns_422(session):
    g = DishGroup(name="G", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    ing = Ingredient(name="NL", unit="kg", min_stock=1, stock_qty=1, is_deleted=False)
    session.add(ing)
    await session.flush()
    d = Dish(name="Món", group_id=g.id, is_deleted=False)
    session.add(d)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    pv = DishPriceVersion(
        dish_id=d.id,
        price=10000,
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
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=1, unit_price=5000)
    session.add(gl)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        receipt_line_id=gl.id,
        quantity_remaining=1,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    await session.flush()
    await session.commit()
    t = DiningTable(name="Bàn X", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 99}]},
        headers=headers,
    )
    assert r.status_code == 422
    assert await order_count(session) == 0


@pytest.mark.anyio
async def test_note_stored(session):
    d, ing, g = await _setup_dish_with_stock(session)
    t = await _setup_table(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1, "GhiChu": "không hành"}]},
        headers=headers,
    )
    assert r.json()["lines"][0]["GhiChu"] == "không hành"


@pytest.mark.anyio
async def test_submit_draws_stock(session):
    d, ing, g = await _setup_dish_with_stock(session, stock_qty=10)
    before = float(ing.stock_qty)
    t = await _setup_table(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 2}]},
        headers=headers,
    )
    assert r.status_code == 201
    after = await ingredient_total(session, d)
    assert after == before - 2


async def _setup_unpriced_dish(session, group_id):
    """A dish with stock and a recipe but no active price version (review #6)."""
    d = Dish(name="Món chưa định giá", group_id=group_id, is_deleted=False)
    session.add(d)
    await session.flush()
    ing = Ingredient(
        name="NL chưa định giá", unit="kg", min_stock=1, stock_qty=10, is_deleted=False
    )
    session.add(ing)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    rc = Recipe(
        dish_id=d.id, business_date=bd, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới"
    )
    session.add(rc)
    await session.flush()
    session.add(RecipeItem(recipe_id=rc.id, ingredient_id=ing.id, quantity=1))
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=10, unit_price=1000)
    session.add(gl)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        receipt_line_id=gl.id,
        quantity_remaining=10,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    await session.flush()
    await session.commit()
    return d


@pytest.mark.anyio
async def test_rejected_when_no_active_price(session):
    """Review #6: a dish without an active price must not be snapshotted at 0 dong."""
    d, ing, g = await _setup_dish_with_stock(session)
    unpriced = await _setup_unpriced_dish(session, g.id)
    t = await _setup_table(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)

    r = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": t.id,
            "lines": [{"MaMon": d.id, "SoLuong": 1}, {"MaMon": unpriced.id, "SoLuong": 1}],
        },
        headers=headers,
    )

    assert r.status_code == 201, r.text
    assert [x["MaMon"] for x in r.json()["lines"]] == [d.id]
    assert r.json()["rejected"] == [{"MaMon": unpriced.id, "reason": "Món chưa có giá"}]


@pytest.mark.anyio
async def test_add_line_rejects_a_dish_without_an_active_price(session):
    """Review #6: adding an unpriced dish to an open order must fail, not snapshot 0 dong."""
    d, ing, g = await _setup_dish_with_stock(session)
    unpriced = await _setup_unpriced_dish(session, g.id)
    t = await _setup_table(session)
    client = await _make_client(session)
    headers = await _cashier_headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=headers,
    )
    oid = r.json()["MaOrder"]

    add = await client.post(
        f"/api/v1/sales/orders/{oid}/lines",
        json={"MaMon": unpriced.id, "SoLuong": 1},
        headers=headers,
    )

    assert add.status_code == 422
