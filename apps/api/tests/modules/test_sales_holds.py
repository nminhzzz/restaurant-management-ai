"""Ingredient holds: reserve lots, never deduct, consume exactly once."""

from datetime import timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

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
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockMovement,
)
from app.modules.sales.models import OrderLine, Reservation
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.enums import VersionStatus


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session):
    await seed_reference_data(session)
    user = User(
        username="cashier_hold",
        password_hash=hash_password("pass"),
        full_name="Cashier",
        role_id="CASHIER",
        status="Hoạt động",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    token = create_access_token(str(user.id), {"role": "CASHIER", "username": user.username})
    return {"Authorization": f"Bearer {token}"}, user


async def _setup(session, stock: int = 10):
    group = DishGroup(name="Nhóm giữ chỗ", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Món giữ chỗ", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    ingredient = Ingredient(
        name="NL giữ chỗ", unit="kg", min_stock=1, stock_qty=stock, is_deleted=False
    )
    session.add(ingredient)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    price = DishPriceVersion(
        dish_id=dish.id,
        price=50000,
        business_date=bd,
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    recipe = Recipe(
        dish_id=dish.id,
        business_date=bd,
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    session.add_all([price, recipe])
    await session.flush()
    session.add(RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=1))
    receipt = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(receipt)
    await session.flush()
    line = GoodsReceiptLine(
        receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=stock, unit_price=1000
    )
    session.add(line)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ingredient.id,
            receipt_line_id=line.id,
            quantity_remaining=stock,
            status="Còn hạn",
            received_at=business_date.now(),
        )
    )
    table = DiningTable(name="Bàn giữ chỗ", is_deleted=False, status="Trống")
    session.add(table)
    await session.flush()
    await session.commit()
    return dish, ingredient, table


async def _hold(client, headers, dish, table, quantity=2, order_id=None):
    body = {
        "table_id": table.id,
        "dish_id": dish.id,
        "quantity": quantity,
        "note": "ít đá",
    }
    if order_id is not None:
        body["order_id"] = order_id
    return await client.post(
        "/api/v1/sales/holds",
        json=body,
        headers=headers,
    )


@pytest.mark.anyio
async def test_a_hold_reserves_without_deducting_stock(session):
    dish, ingredient, table = await _setup(session, stock=10)
    client = await _make_client(session)
    headers, _ = await _headers(session)

    response = await _hold(client, headers, dish, table, quantity=2)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["SoLuong"] == 2
    assert body["DonGia"] == 50000
    await session.refresh(ingredient)
    assert float(ingredient.stock_qty) == 10
    assert len(body["MaLuotChon"]) == 32
    listed = await client.get(
        f"/api/v1/sales/holds?selection_code={body['MaLuotChon']}", headers=headers
    )
    assert [row["MaGiuCho"] for row in listed.json()] == [body["MaGiuCho"]]


@pytest.mark.anyio
async def test_two_holds_cannot_overbook_the_same_lots(session):
    dish, _, table = await _setup(session, stock=3)
    client = await _make_client(session)
    headers, _ = await _headers(session)

    first = await _hold(client, headers, dish, table, quantity=2)
    second = await _hold(client, headers, dish, table, quantity=2)

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["error"]["message"] == "Không đủ tồn kho khả dụng."


@pytest.mark.anyio
async def test_sending_a_hold_consumes_it_exactly_once(session):
    dish, ingredient, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()

    first = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": table.id,
            "lines": [{"MaMon": dish.id, "SoLuong": 2, "hold_id": hold["MaGiuCho"]}],
        },
        headers=headers,
    )

    assert first.status_code == 201, first.text
    assert first.json()["lines"][0]["MaPhienBanGia"] is not None
    await session.refresh(ingredient)
    assert float(ingredient.stock_qty) == 3
    order_id = first.json()["MaOrder"]
    movements = await session.scalar(
        select(func.count())
        .select_from(StockMovement)
        .where(StockMovement.order_line_id.is_not(None))
    )
    assert movements == 1
    assert (
        await session.scalar(
            select(func.count()).select_from(OrderLine).where(OrderLine.order_id == order_id)
        )
        == 1
    )

    second = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": table.id,
            "lines": [{"MaMon": dish.id, "SoLuong": 2, "hold_id": hold["MaGiuCho"]}],
        },
        headers=headers,
    )
    assert second.status_code == 422
    await session.refresh(ingredient)
    assert float(ingredient.stock_qty) == 3


@pytest.mark.anyio
async def test_releasing_a_hold_frees_capacity(session):
    dish, _, table = await _setup(session, stock=3)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    first = (await _hold(client, headers, dish, table, quantity=2)).json()
    assert (await _hold(client, headers, dish, table, quantity=2)).status_code == 422

    released = await client.delete(f"/api/v1/sales/holds/{first['MaGiuCho']}", headers=headers)
    assert released.status_code == 200
    assert (await _hold(client, headers, dish, table, quantity=2)).status_code == 201


@pytest.mark.anyio
async def test_an_expired_hold_stops_occupying_capacity(session):
    dish, _, table = await _setup(session, stock=3)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    first = (await _hold(client, headers, dish, table, quantity=2)).json()
    hold = await session.get(Reservation, first["MaGiuCho"])
    hold.expires_at = business_date.now().replace(tzinfo=None) - timedelta(minutes=1)
    await session.commit()

    assert (await _hold(client, headers, dish, table, quantity=2)).status_code == 201
    listed = await client.get("/api/v1/sales/holds", headers=headers)
    assert all(row["MaGiuCho"] != first["MaGiuCho"] for row in listed.json())


@pytest.mark.anyio
async def test_increasing_a_hold_checks_the_extra_capacity(session):
    dish, _, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()

    increased = await client.patch(
        f"/api/v1/sales/holds/{hold['MaGiuCho']}", json={"quantity": 4}, headers=headers
    )
    overbooked = await client.patch(
        f"/api/v1/sales/holds/{hold['MaGiuCho']}", json={"quantity": 6}, headers=headers
    )

    assert increased.status_code == 200
    assert increased.json()["SoLuong"] == 4
    assert overbooked.status_code == 422


@pytest.mark.anyio
async def test_decreasing_a_hold_frees_capacity(session):
    dish, _, table = await _setup(session, stock=3)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()

    decreased = await client.patch(
        f"/api/v1/sales/holds/{hold['MaGiuCho']}", json={"quantity": 1}, headers=headers
    )
    assert decreased.status_code == 200
    assert (await _hold(client, headers, dish, table, quantity=2)).status_code == 201


@pytest.mark.anyio
async def test_an_open_order_can_hold_and_send_an_extra_line(session):
    dish, ingredient, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    created = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
        headers=headers,
    )
    order_id = created.json()["MaOrder"]

    hold = await _hold(client, headers, dish, table, quantity=1, order_id=order_id)
    assert hold.status_code == 201, hold.text
    added = await client.post(
        f"/api/v1/sales/orders/{order_id}/lines",
        json={"MaMon": dish.id, "SoLuong": 1, "hold_id": hold.json()["MaGiuCho"]},
        headers=headers,
    )
    assert added.status_code == 201, added.text
    await session.refresh(ingredient)
    assert float(ingredient.stock_qty) == 3


@pytest.mark.anyio
async def test_menu_availability_drops_after_a_hold(session):
    dish, _, table = await _setup(session, stock=5)
    client = await _make_client(session)
    headers, _ = await _headers(session)

    before = (await client.get("/api/v1/catalog/dishes?size=200", headers=headers)).json()
    assert next(row for row in before["items"] if row["MaMon"] == dish.id)["SoSuatKhaDung"] == 5

    assert (await _hold(client, headers, dish, table, quantity=2)).status_code == 201
    after = (await client.get("/api/v1/catalog/dishes?size=200", headers=headers)).json()
    assert next(row for row in after["items"] if row["MaMon"] == dish.id)["SoSuatKhaDung"] == 3


@pytest.mark.anyio
async def test_an_expired_hold_is_rechecked_and_needs_explicit_confirmation(session):
    """R16/FR-SALE-05: never renew silently, but let the cashier confirm."""
    from datetime import timedelta

    from app.modules.sales.models import Reservation

    dish, _, table = await _setup(session, stock=10)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()

    reservation = await session.get(Reservation, hold["MaGiuCho"])
    reservation.expires_at = business_date.now() - timedelta(minutes=1)
    await session.commit()

    refused = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": table.id,
            "lines": [{"MaMon": dish.id, "SoLuong": 2, "hold_id": hold["MaGiuCho"]}],
        },
        headers=headers,
    )
    assert refused.status_code == 422
    assert "hết hạn" in refused.json()["error"]["message"]

    accepted = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": table.id,
            "XacNhanHetHan": True,
            "lines": [{"MaMon": dish.id, "SoLuong": 2, "hold_id": hold["MaGiuCho"]}],
        },
        headers=headers,
    )
    assert accepted.status_code == 201, accepted.text
    assert accepted.json()["lines"][0]["SoLuong"] == 2


@pytest.mark.anyio
async def test_bulk_add_honours_the_expired_hold_confirmation(session):
    """P2: the bulk path must pass XacNhanHetHan down to the per-line handler."""
    from datetime import timedelta

    from app.modules.sales.models import Reservation

    dish, _, table = await _setup(session, stock=10)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    created = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
        headers=headers,
    )
    order_id = created.json()["MaOrder"]
    hold = await _hold(client, headers, dish, table, quantity=1, order_id=order_id)
    reservation = await session.get(Reservation, hold.json()["MaGiuCho"])
    reservation.expires_at = business_date.now() - timedelta(minutes=1)
    await session.commit()

    added = await client.post(
        f"/api/v1/sales/orders/{order_id}/lines/bulk",
        json={
            "XacNhanHetHan": True,
            "lines": [{"dish_id": dish.id, "quantity": 1, "hold_id": hold.json()["MaGiuCho"]}],
        },
        headers=headers,
    )

    assert added.status_code == 201, added.text


@pytest.mark.anyio
async def test_active_hold_requires_confirmation_when_price_changes(session):
    from sqlalchemy import select

    from app.modules.catalog.models import DishPriceVersion

    dish, ingredient, table = await _setup(session, stock=10)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    hold = (await _hold(client, headers, dish, table, quantity=2)).json()
    old = (await session.execute(select(DishPriceVersion))).scalar_one()
    old.status = "Hết hiệu lực"
    price = DishPriceVersion(
        dish_id=dish.id,
        price=70000,
        business_date=business_date.business_date_of(business_date.now()),
        status="Đang áp dụng",
        change_type="Cập nhật",
    )
    session.add(price)
    await session.commit()
    payload = {
        "MaBan": table.id,
        "lines": [{"MaMon": dish.id, "SoLuong": 2, "hold_id": hold["MaGiuCho"]}],
    }
    rejected = await client.post("/api/v1/sales/orders", json=payload, headers=headers)
    assert rejected.status_code == 422, rejected.text
    assert "thay đổi" in rejected.text.lower()
    payload["confirm_expired"] = True
    accepted = await client.post("/api/v1/sales/orders", json=payload, headers=headers)
    assert accepted.status_code == 201, accepted.text
    from app.modules.sales.models import OrderLine

    line = await session.get(OrderLine, accepted.json()["lines"][0]["MaChiTietOrder"])
    assert line.unit_price == 70000
    await session.refresh(ingredient)
    assert ingredient.stock_qty == 8
