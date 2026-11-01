"""Database-level integrity rules from document 04 part G (quantities positive, lots coherent)."""

from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from app.modules.catalog.models import Dish, DishPriceVersion, Ingredient, Recipe, RecipeItem
from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot

pytestmark = pytest.mark.anyio


async def _ingredient(session) -> Ingredient:
    ingredient = Ingredient(name="NL ràng buộc", unit="kg", stock_qty=0)
    session.add(ingredient)
    await session.flush()
    return ingredient


async def _rejected(session, *rows) -> None:
    session.add_all(rows)
    with pytest.raises(IntegrityError):
        await session.flush()
    await session.rollback()


async def test_a_price_version_must_have_a_positive_price(session):
    dish = Dish(name="Món giá 0", missing_recipe=True)
    session.add(dish)
    await session.flush()
    await _rejected(
        session,
        DishPriceVersion(
            dish_id=dish.id,
            price=Decimal(0),
            business_date=date(2026, 9, 1),
            status="Đang áp dụng",
            change_type="Tạo mới",
        ),
    )


async def test_a_recipe_line_must_have_a_positive_quantity(session):
    dish = Dish(name="Món công thức", missing_recipe=False)
    ingredient = await _ingredient(session)
    session.add(dish)
    await session.flush()
    recipe = Recipe(dish_id=dish.id, business_date=date(2026, 9, 1), status="Đang áp dụng")
    session.add(recipe)
    await session.flush()
    await _rejected(
        session, RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=Decimal(0))
    )


async def test_a_receipt_line_needs_positive_quantity_and_factor(session):
    ingredient = await _ingredient(session)
    receipt = GoodsReceipt(receipt_date=datetime(2026, 9, 1, 9))
    session.add(receipt)
    await session.flush()
    await _rejected(
        session,
        GoodsReceiptLine(
            receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=Decimal(0), unit_price=1
        ),
    )


async def test_a_lot_cannot_hold_negative_stock_or_start_empty(session):
    ingredient = await _ingredient(session)
    await _rejected(
        session,
        IngredientLot(
            ingredient_id=ingredient.id, quantity_remaining=Decimal(-1), received_quantity=1
        ),
    )
    ingredient = await _ingredient(session)
    await _rejected(
        session,
        IngredientLot(
            ingredient_id=ingredient.id, quantity_remaining=Decimal(0), received_quantity=Decimal(0)
        ),
    )


async def test_an_adjustment_lot_never_points_at_a_receipt_line(session):
    ingredient = await _ingredient(session)
    receipt = GoodsReceipt(receipt_date=datetime(2026, 9, 1, 9))
    session.add(receipt)
    await session.flush()
    line = GoodsReceiptLine(
        receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=Decimal(1), unit_price=1
    )
    session.add(line)
    await session.flush()
    await _rejected(
        session,
        IngredientLot(
            ingredient_id=ingredient.id,
            receipt_line_id=line.id,
            quantity_remaining=Decimal(1),
            received_quantity=Decimal(1),
            is_adjustment=True,
        ),
    )


async def test_a_lot_without_an_explicit_received_quantity_starts_with_what_it_holds(session):
    ingredient = await _ingredient(session)
    lot = IngredientLot(ingredient_id=ingredient.id, quantity_remaining=Decimal(7))
    session.add(lot)
    await session.flush()
    assert lot.received_quantity == 7
