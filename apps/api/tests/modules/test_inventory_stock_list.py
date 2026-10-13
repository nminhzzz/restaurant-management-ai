"""FR-INV-07 low-stock flag, FR-INV-12 stock listing with search/filter."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot
from app.modules.settings.models import SystemConfig, User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="WAREHOUSE", username="kho03"):
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


async def _stocked(session, name: str, quantity: int, **kwargs) -> Ingredient:
    """An ingredient whose book stock is backed by one sellable lot (FR-INV-10)."""
    ingredient = Ingredient(name=name, unit="kg", stock_qty=quantity, is_deleted=False, **kwargs)
    session.add(ingredient)
    await session.flush()
    session.add(IngredientLot(ingredient_id=ingredient.id, quantity_remaining=Decimal(quantity)))
    await session.flush()
    return ingredient


@pytest.mark.anyio
async def test_low_stock_uses_ingredient_threshold_when_set(session):
    ing = await _stocked(session, "Muối", 3, min_stock=10)
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock", headers=h)
    assert r.status_code == 200
    row = next(x for x in r.json()["items"] if x["MaNguyenLieu"] == ing.id)
    assert row["MucTonToiThieuApDung"] == 10
    assert row["CanhBaoTonThap"] is True


@pytest.mark.anyio
async def test_low_stock_falls_back_to_the_live_system_default_when_no_threshold_is_set(session):
    # System default is seeded at 5 (see conftest); NULL means "use the default".
    ing = await _stocked(session, "Đường", 3)
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock", headers=h)
    row = next(x for x in r.json()["items"] if x["MaNguyenLieu"] == ing.id)
    assert row["MucTonToiThieuApDung"] == 5
    assert row["CanhBaoTonThap"] is True

    cfg = await session.get(SystemConfig, 1)
    cfg.default_stock_threshold = 2
    await session.commit()
    r = await client.get("/api/v1/inventory/stock", headers=h)
    row = next(x for x in r.json()["items"] if x["MaNguyenLieu"] == ing.id)
    assert row["MucTonToiThieuApDung"] == 2
    assert row["CanhBaoTonThap"] is False


@pytest.mark.anyio
async def test_an_explicit_zero_threshold_is_not_the_default(session):
    ing = await _stocked(session, "Tiêu", 1, min_stock=0)
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock", headers=h)
    row = next(x for x in r.json()["items"] if x["MaNguyenLieu"] == ing.id)
    assert row["MucTonToiThieuApDung"] == 0
    assert row["CanhBaoTonThap"] is False


@pytest.mark.anyio
async def test_the_alert_compares_available_stock_not_book_stock(session):
    """FR-INV-07: expired lots count in the book stock but not in the availability."""
    ing = Ingredient(name="Sữa", unit="l", stock_qty=10, min_stock=5, is_deleted=False)
    session.add(ing)
    await session.flush()
    session.add_all(
        [
            IngredientLot(ingredient_id=ing.id, quantity_remaining=Decimal(2)),
            IngredientLot(
                ingredient_id=ing.id,
                quantity_remaining=Decimal(8),
                expiry_date=date(2020, 1, 1),
            ),
        ]
    )
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock", headers=h)
    row = next(x for x in r.json()["items"] if x["MaNguyenLieu"] == ing.id)
    assert row["SoLuongTon"] == 10
    assert row["SoLuongKhaDung"] == 2
    assert row["SoLuongGiu"] == 0
    assert row["CanhBaoTonThap"] is True


@pytest.mark.anyio
async def test_stock_above_threshold_not_flagged(session):
    ing = await _stocked(session, "Gạo tẻ", 50, min_stock=2)
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock", headers=h)
    row = next(x for x in r.json()["items"] if x["MaNguyenLieu"] == ing.id)
    assert row["CanhBaoTonThap"] is False


@pytest.mark.anyio
async def test_stock_search_by_name(session):
    session.add_all(
        [
            Ingredient(name="Cà chua", unit="kg", min_stock=1, stock_qty=10, is_deleted=False),
            Ingredient(name="Cà rốt", unit="kg", min_stock=1, stock_qty=10, is_deleted=False),
            Ingredient(name="Hành tây", unit="kg", min_stock=1, stock_qty=10, is_deleted=False),
        ]
    )
    await session.flush()
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock?search=Cà", headers=h)
    assert r.status_code == 200
    names = {row["TenNguyenLieu"] for row in r.json()["items"]}
    assert names == {"Cà chua", "Cà rốt"}


@pytest.mark.anyio
async def test_stock_filter_alerting_true_returns_only_low_rows(session):
    await _stocked(session, "A1", 1, min_stock=10)
    await _stocked(session, "A2", 100, min_stock=1)
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock?alerting=true", headers=h)
    names = {row["TenNguyenLieu"] for row in r.json()["items"]}
    assert names == {"A1"}


@pytest.mark.anyio
async def test_stock_total_reflects_all_rows_across_pages(session):
    """FR-INV-12: `total` must count every matching row, not just the page returned."""
    session.add_all(
        [
            Ingredient(name=f"NL{i}", unit="kg", min_stock=1, stock_qty=10, is_deleted=False)
            for i in range(5)
        ]
    )
    await session.flush()
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock?page=1&page_size=2", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 5
    assert len(body["items"]) == 2


@pytest.mark.anyio
async def test_deleted_ingredient_excluded_from_stock_list(session):
    ing = Ingredient(name="Đã xóa", unit="kg", min_stock=1, stock_qty=10, is_deleted=True)
    session.add(ing)
    await session.flush()
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/stock", headers=h)
    ids = {row["MaNguyenLieu"] for row in r.json()["items"]}
    assert ing.id not in ids


@pytest.mark.anyio
async def test_lot_expiry_uses_today_and_persisted_warning_boundary(session, monkeypatch):
    await seed_reference_data(session)
    cfg = await session.get(SystemConfig, 1)
    assert cfg is not None
    cfg.expiry_warning_days = 4
    ing = Ingredient(name="Bột", unit="kg", stock_qty=15, is_deleted=False)
    session.add(ing)
    await session.flush()
    today = date(2031, 4, 5)
    monkeypatch.setattr(business_date, "now", lambda: datetime(2031, 4, 5, 12))
    dates = [
        today - timedelta(days=1),
        today,
        today + timedelta(days=4),
        today + timedelta(days=5),
        None,
    ]
    lots = [
        IngredientLot(
            ingredient_id=ing.id,
            quantity_remaining=Decimal("2.5"),
            expiry_date=expiry,
            status="Còn hạn" if index == 0 else "Hết hạn",
        )
        for index, expiry in enumerate(dates)
    ]
    session.add_all(lots)
    await session.commit()
    client = await _make_client(session)
    headers, _ = await _headers(session)
    response = await client.get("/api/v1/inventory/lots", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    rows = {row["MaLoNguyenLieu"]: row for row in body["items"]}
    assert [rows[lot.id]["TrangThaiHanSuDung"] for lot in lots] == [
        "Hết hạn",
        "Sắp hết hạn",
        "Sắp hết hạn",
        "Còn hạn",
        "Còn hạn",
    ]
    assert rows[lots[0].id]["TenNguyenLieu"] == "Bột"
    assert rows[lots[0].id]["SoLuongConLai"] == 2.5
    assert rows[lots[0].id]["HanSuDung"] == dates[0].isoformat()
    assert rows[lots[4].id]["HanSuDung"] is None


@pytest.mark.anyio
async def test_lot_expiry_pagination_is_stable_and_role_protected(session):
    ing = Ingredient(name="Gạo", unit="kg", stock_qty=3, is_deleted=False)
    session.add(ing)
    await session.flush()
    session.add_all(
        [IngredientLot(ingredient_id=ing.id, quantity_remaining=Decimal("1")) for _ in range(3)]
    )
    await session.commit()
    client = await _make_client(session)
    warehouse, _ = await _headers(session)
    first = await client.get("/api/v1/inventory/lots?page=1&page_size=2", headers=warehouse)
    second = await client.get("/api/v1/inventory/lots?page=2&page_size=2", headers=warehouse)
    assert first.status_code == second.status_code == 200
    assert first.json()["total"] == second.json()["total"] == 3
    assert len(first.json()["items"]) == 2
    assert len(second.json()["items"]) == 1
    assert {row["MaLoNguyenLieu"] for row in first.json()["items"]}.isdisjoint(
        {row["MaLoNguyenLieu"] for row in second.json()["items"]}
    )
    manager, _ = await _headers(session, "MANAGER", "manager_lots")
    assert (await client.get("/api/v1/inventory/lots", headers=manager)).status_code == 200
    cashier, _ = await _headers(session, "CASHIER", "cashier_lots")
    assert (await client.get("/api/v1/inventory/lots", headers=cashier)).status_code == 403
