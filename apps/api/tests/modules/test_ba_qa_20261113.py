"""Regressions for the BA decisions of 2026-11-13 on 7b50a8a (PH-04: the 'Hủy nhập' kind)."""

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.modules.catalog.models import Ingredient
from app.modules.inventory import service as inventory
from app.modules.inventory.models import GoodsReceiptLine, IngredientLot, StockMovement
from app.shared import business_date

pytestmark = pytest.mark.anyio


async def _ingredient(session, name="Thịt bò"):
    ing = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    session.add(ing)
    await session.flush()
    return ing


async def test_cancelled_receipt_line_is_reversed_as_huy_nhap(session, active_user):
    ing = await _ingredient(session)
    receipt = await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 8, "unit_price": 1000}],
    )
    line = await session.scalar(
        select(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt.id)
    )
    lot = await session.scalar(
        select(IngredientLot).where(IngredientLot.receipt_line_id == line.id)
    )

    await inventory.cancel_receipt(session, active_user.id, receipt.id)

    reversal = (
        await session.scalars(
            select(StockMovement)
            .where(StockMovement.ingredient_id == ing.id)
            .order_by(StockMovement.id.desc())
            .limit(1)
        )
    ).one()
    assert reversal.kind == "Hủy nhập"
    assert reversal.receipt_line_id == line.id
    assert reversal.lot_id == lot.id
    assert reversal.order_line_id is None
    assert Decimal(str(reversal.qty)) == -Decimal(str(line.quantity))


async def test_hoan_kho_must_point_at_an_order_line(session, active_user):
    ing = await _ingredient(session)
    receipt = await inventory.create_receipt(
        session,
        active_user.id,
        None,
        None,
        [{"ingredient_id": ing.id, "quantity": 2, "unit_price": 1000}],
    )
    line = await session.scalar(
        select(GoodsReceiptLine).where(GoodsReceiptLine.receipt_id == receipt.id)
    )
    session.add(
        StockMovement(
            ingredient_id=ing.id,
            kind="Hoàn kho",
            qty=-2,
            business_date=business_date.business_date_of(business_date.now()),
            receipt_line_id=line.id,
        )
    )
    with pytest.raises(IntegrityError):
        await session.flush()
