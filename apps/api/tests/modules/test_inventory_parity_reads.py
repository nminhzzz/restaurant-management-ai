"""Inventory read contracts required by FR-INV-07/12 and UC 3.2/3.5."""

from datetime import timedelta
from decimal import Decimal

import pytest

from app.modules.catalog.models import Ingredient
from app.modules.inventory import service
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales.models import Reservation, ReservationDetail
from app.shared import business_date


@pytest.mark.asyncio
async def test_stock_separates_book_eligible_held_and_available(session):
    now = business_date.now()
    today = business_date.business_date_of(now)
    ingredient = Ingredient(name="Gạo", unit="kg", stock_qty=100, min_stock=65)
    session.add(ingredient)
    await session.flush()
    valid = IngredientLot(
        ingredient_id=ingredient.id,
        quantity_remaining=80,
        received_at=now,
        expiry_date=today + timedelta(days=2),
        is_adjustment=True,
    )
    expired = IngredientLot(
        ingredient_id=ingredient.id,
        quantity_remaining=20,
        received_at=now - timedelta(days=4),
        expiry_date=today - timedelta(days=1),
        is_adjustment=True,
    )
    session.add_all([valid, expired])
    await session.flush()
    for code, minutes, qty in [("active", 5, 25), ("expired", -1, 10)]:
        hold = Reservation(
            selection_code=code,
            user_id=1,
            dish_id=1,
            quantity=1,
            expires_at=now + timedelta(minutes=minutes),
            status="Đang giữ",
        )
        session.add(hold)
        await session.flush()
        session.add(ReservationDetail(reservation_id=hold.id, lot_id=valid.id, quantity=qty))
    await session.flush()

    rows, total = await service.list_stock(session, alerting=True)
    assert total == 1, "Low stock is measured on available quantity, not book quantity"
    assert rows[0].get("SoLuongTon") == 100
    assert rows[0].get("SoLuongDuDieuKien") == 80
    assert rows[0].get("SoLuongGiu") == 25
    assert rows[0].get("SoLuongKhaDung") == 55
    assert rows[0].get("DonViTinh") == "kg"
    assert rows[0].get("ThoiDiemTinh") == now.isoformat()


@pytest.mark.asyncio
async def test_lot_history_filters_and_retains_source_links(session):
    from app.modules.inventory.queries import list_lots, list_movements

    now = business_date.now()
    ingredient = Ingredient(name="Muối", unit="kg", stock_qty=5, min_stock=0)
    session.add(ingredient)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ingredient.id,
        quantity_remaining=5,
        received_at=now,
        is_adjustment=True,
    )
    session.add(lot)
    await session.flush()
    session.add(
        StockMovement(
            ingredient_id=ingredient.id,
            lot_id=lot.id,
            kind="Hoàn kho",
            qty=Decimal(5),
            order_line_id=17,
            business_date=business_date.business_date_of(now),
            occurred_at=now,
        )
    )
    await session.flush()
    lots, total = await list_lots(session, ingredient_id=ingredient.id, page=1, page_size=1)
    assert total == 1
    assert lots[0]["MaLoNguyenLieu"] == lot.id
    assert lots[0]["SoLuongKhaDung"] == 5
    movements, total = await list_movements(session, lot_id=lot.id, kind="Hoàn kho")
    assert total == 1
    assert movements[0]["MaChiTietOrder"] == 17
    assert movements[0]["SoLuongThayDoi"] == 5
    assert (await list_movements(session, kind="Nhập"))[1] == 0


@pytest.mark.asyncio
async def test_an_expiring_lot_has_its_own_state(session):
    """FR-INV-14: Còn hạn / Sắp hết hạn / Hết hạn are three distinct states."""
    from app.modules.inventory.queries import list_lots

    now = business_date.now()
    today = business_date.business_date_of(now)
    ingredient = Ingredient(name="Sữa", unit="l", stock_qty=2, min_stock=0)
    session.add(ingredient)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ingredient.id,
            quantity_remaining=2,
            received_at=now - timedelta(days=5),
            expiry_date=today + timedelta(days=1),
            is_adjustment=True,
        )
    )
    await session.flush()

    rows, _ = await list_lots(session, ingredient_id=ingredient.id)
    assert rows[0]["TrangThai"] == "Sắp hết hạn"

    filtered, _ = await list_lots(session, ingredient_id=ingredient.id, status="Sắp hết hạn")
    assert len(filtered) == 1
