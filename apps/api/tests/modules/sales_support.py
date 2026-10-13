"""Builders shared by the sales review-gap tests: a sellable dish, tables, staff, an API client."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

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


@dataclass
class Sellable:
    dish: Dish
    ingredient: Ingredient
    lots: list[IngredientLot]


async def api(session) -> AsyncClient:
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def staff(session, role: str, username: str | None = None) -> tuple[dict, User]:
    await seed_reference_data(session)
    name = username or f"{role.lower()}-user"
    user = (await session.execute(select(User).where(User.username == name))).scalar_one_or_none()
    if user is None:
        user = User(
            username=name,
            password_hash=hash_password("pass"),
            full_name=name,
            role_id=role,
            status="Hoạt động",
        )
        session.add(user)
        await session.flush()
        await session.commit()
    return {"Authorization": f"Bearer {create_access_token(str(user.id))}"}, user


async def table(session, name: str = "Bàn 1") -> DiningTable:
    row = DiningTable(name=name, is_deleted=False, status="Trống")
    session.add(row)
    await session.flush()
    await session.commit()
    return row


async def sellable(
    session,
    *,
    name: str = "Món",
    price: int | None = 50000,
    per_portion: float = 1,
    lots: list[tuple[float, datetime, date | None]] | None = None,
    group: DishGroup | None = None,
    missing_recipe: bool = False,
    with_recipe: bool = True,
) -> Sellable:
    """A dish with a price, a recipe and ingredient lots `(quantity, received_at, expiry)`."""
    if group is None:
        group = DishGroup(name=f"Nhóm {name}", display_order=1, is_deleted=False)
        session.add(group)
        await session.flush()
    dish = Dish(name=name, group_id=group.id, is_deleted=False, missing_recipe=missing_recipe)
    session.add(dish)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    if price is not None:
        session.add(
            DishPriceVersion(
                dish_id=dish.id,
                price=price,
                business_date=bd,
                status=VersionStatus.HIEU_LUC.value,
                change_type="Tạo mới",
            )
        )
    lots_spec = lots if lots is not None else [(20, business_date.now(), None)]
    total = sum(quantity for quantity, _, _ in lots_spec)
    ingredient = Ingredient(
        name=f"NL {name}", unit="kg", min_stock=1, stock_qty=total, is_deleted=False
    )
    session.add(ingredient)
    await session.flush()
    if with_recipe:
        recipe = Recipe(
            dish_id=dish.id,
            business_date=bd,
            status=VersionStatus.HIEU_LUC.value,
            change_type="Tạo mới",
        )
        session.add(recipe)
        await session.flush()
        session.add(
            RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=per_portion)
        )
    receipt = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(receipt)
    await session.flush()
    rows = []
    for quantity, received_at, expiry in lots_spec:
        line = GoodsReceiptLine(
            receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=quantity, unit_price=1000
        )
        session.add(line)
        await session.flush()
        lot = IngredientLot(
            ingredient_id=ingredient.id,
            receipt_line_id=line.id,
            quantity_remaining=quantity,
            status="Còn hạn",
            received_at=received_at,
            expiry_date=expiry,
        )
        session.add(lot)
        rows.append(lot)
    await session.flush()
    await session.commit()
    return Sellable(dish=dish, ingredient=ingredient, lots=rows)


async def place_order(client, headers, dish_table, items: list[tuple[int, int]]) -> dict:
    """POST /sales/orders for a dine-in order; returns the response body."""
    response = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": dish_table.id,
            "lines": [{"MaMon": dish_id, "SoLuong": quantity} for dish_id, quantity in items],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def minutes(delta: int) -> timedelta:
    return timedelta(minutes=delta)


async def add_ingredient_to_recipe(
    session, world: Sellable, *, per_portion: float, quantity: float
) -> tuple[Ingredient, IngredientLot]:
    """A second ingredient (one lot) in the dish's active recipe."""
    recipe_id = (
        await session.execute(select(Recipe.id).where(Recipe.dish_id == world.dish.id))
    ).scalar_one()
    ingredient = Ingredient(
        name=f"NL phụ {world.dish.id}", unit="kg", min_stock=1, stock_qty=quantity, is_deleted=False
    )
    session.add(ingredient)
    await session.flush()
    session.add(RecipeItem(recipe_id=recipe_id, ingredient_id=ingredient.id, quantity=per_portion))
    receipt = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(receipt)
    await session.flush()
    line = GoodsReceiptLine(
        receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=quantity, unit_price=1000
    )
    session.add(line)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ingredient.id,
        receipt_line_id=line.id,
        quantity_remaining=quantity,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    await session.commit()
    return ingredient, lot
