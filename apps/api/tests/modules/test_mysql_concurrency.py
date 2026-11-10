"""Races that only a real MySQL can show: SQLite ignores `SELECT ... FOR UPDATE`.

Both cases need a migrated, disposable MySQL database with no dishes waiting in the kitchen
and no unsent selections (a stocktake cannot open otherwise):

    MYSQL_TEST_DATABASE_URL=mysql+asyncmy://.../restaurant_test pytest -m integration \
        tests/modules/test_mysql_concurrency.py
"""

import asyncio
import os
from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core import database
from app.core.errors import BusinessRuleError
from app.modules.catalog import service as catalog
from app.modules.catalog.models import DiningTable, Ingredient
from app.modules.inventory import service as inventory
from app.modules.inventory.models import Stocktake
from app.modules.sales import orders
from app.modules.settings import service as settings
from app.shared.roles import Role

pytestmark = pytest.mark.integration

DISPOSABLE_PREFIXES = ("restaurant_test", "restaurant_acceptance", "restaurant_verify")
SEND_ROUNDS = 20
STOCKTAKE_ROUNDS = 100


@asynccontextmanager
async def _application_on_test_database():
    """Point the application's own engines at the disposable database for one test."""
    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MYSQL_TEST_DATABASE_URL to a migrated, disposable MySQL database")
    if not (make_url(url).database or "").startswith(DISPOSABLE_PREFIXES):
        pytest.fail(f"MYSQL_TEST_DATABASE_URL must name one of {DISPOSABLE_PREFIXES}")
    previous = (database._engine, database._counter_engine, database._session_factory)
    engine = create_async_engine(url, pool_pre_ping=True)
    database._engine, database._counter_engine, database._session_factory = engine, None, None
    try:
        yield database.get_session_factory()
    finally:
        if database._counter_engine is not None:
            await database._counter_engine.dispose()
        await engine.dispose()
        database._engine, database._counter_engine, database._session_factory = previous


async def _reference_data(factory) -> None:
    async with factory() as session:
        await settings.seed_reference_data(session)
        await session.commit()


@pytest.mark.asyncio
async def test_two_cashiers_sending_to_the_same_free_table_get_one_order():
    """TC-SALE-49: one order takes the table; the other send is refused and draws nothing."""
    async with _application_on_test_database() as factory:
        await _reference_data(factory)
        tag = uuid4().hex[:8]
        async with factory() as session:
            cashiers = [
                (
                    await settings.create_user(
                        session,
                        None,
                        f"tn_{tag}_{index}",
                        "mat-khau-thu",
                        "Thu ngân",
                        None,
                        Role.CASHIER,
                    )
                ).id
                for index in range(2)
            ]
            ingredient = await catalog.create_ingredient(session, None, f"NL {tag}", "g", 0, None)
            group = await catalog.create_group(session, None, f"Nhóm {tag}")
            dish = await catalog.create_dish(session, None, f"Món {tag}", group.id, None, 50000)
            await catalog.apply_price_directly(session, None, dish.id, Decimal(50000))
            await catalog.assign_recipe(session, None, dish.id, [(ingredient.id, Decimal(150))])
            await inventory.create_receipt(
                session,
                cashiers[0],
                None,
                None,
                [
                    {
                        "ingredient_id": ingredient.id,
                        "quantity": 150 * SEND_ROUNDS * 2,
                        "unit_price": 200,
                    }
                ],
            )
            tables = [
                (await catalog.create_table(session, None, f"Bàn {tag}-{index}")).id
                for index in range(SEND_ROUNDS)
            ]
            await session.commit()
            ingredient_id, dish_id = ingredient.id, dish.id

        async def send(cashier_id: int, table_id: int) -> int | None:
            async with factory() as session:
                try:
                    result = await orders.submit_order(
                        session,
                        {
                            "table_id": table_id,
                            "order_type": "Tại chỗ",
                            "lines": [{"MaMon": dish_id, "SoLuong": 1, "GhiChu": None}],
                        },
                        actor_id=cashier_id,
                    )
                    if result["rejected"]:
                        await session.rollback()
                        return None
                    await session.commit()
                    return result["order"].id
                except BusinessRuleError:
                    await session.rollback()
                    return None

        winners: list[int] = []
        try:
            for table_id in tables:
                sent = await asyncio.gather(*(send(cashier, table_id) for cashier in cashiers))
                accepted = [order_id for order_id in sent if order_id is not None]
                assert len(accepted) == 1, f"table {table_id}: {sent}"
                winners.extend(accepted)
                async with factory() as session:
                    table = await session.get(DiningTable, table_id)
                    assert table.current_order_id == accepted[0]
            async with factory() as session:
                stock = (await session.get(Ingredient, ingredient_id)).stock_qty
            # Only the accepted sends drew stock: one serving of 150 g per table.
            assert stock == 150 * SEND_ROUNDS * 2 - 150 * SEND_ROUNDS
        finally:
            # Waiting dishes would stop the next stocktake from opening.
            async with factory() as session:
                for order_id in winners:
                    await orders.cancel_order(
                        session, order_id, "dọn dữ liệu thử", actor_id=cashiers[0]
                    )
                await session.commit()


@pytest.mark.asyncio
async def test_a_receipt_racing_a_stocktake_is_either_counted_or_refused():
    """TC-INV-46: stock never changes between the opening of a session and its confirmation."""
    async with _application_on_test_database() as factory:
        await _reference_data(factory)
        tag = uuid4().hex[:8]
        async with factory() as session:
            ingredient_id = (
                await catalog.create_ingredient(session, None, f"NL kiểm kê {tag}", "g", 0, None)
            ).id
            keeper_id = (
                await settings.create_user(
                    session, None, f"bep_{tag}", "mat-khau-thu", "Bếp", None, Role.WAREHOUSE
                )
            ).id
            await session.commit()

        async def open_session() -> int:
            async with factory() as session:
                stocktake = await inventory.create_stocktake(session, keeper_id)
                await session.commit()
                return stocktake.id

        async def receive() -> bool:
            async with factory() as session:
                try:
                    await inventory.create_receipt(
                        session,
                        keeper_id,
                        None,
                        None,
                        [{"ingredient_id": ingredient_id, "quantity": 1, "unit_price": 1000}],
                    )
                    await session.commit()
                    return True
                except BusinessRuleError as error:
                    await session.rollback()
                    assert "kiểm kê" in error.message
                    return False

        async def stock() -> Decimal:
            async with factory() as session:
                return (await session.get(Ingredient, ingredient_id)).stock_qty

        outcomes = {True: 0, False: 0}
        for _ in range(STOCKTAKE_ROUNDS):
            before = await stock()
            stocktake_id, received = await asyncio.gather(open_session(), receive())
            outcomes[received] += 1
            at_opening = await stock()
            # Committed before the lock: counted. Arrived after it: refused, not half-applied.
            assert at_opening == before + (1 if received else 0)
            assert await receive() is False
            assert await stock() == at_opening

            async with factory() as session:
                counts = [
                    (row_id, quantity, None)
                    for row_id, quantity in await session.execute(
                        select(Ingredient.id, Ingredient.stock_qty).where(
                            Ingredient.is_deleted.is_(False)
                        )
                    )
                ]
                await inventory.record_counts(session, stocktake_id, counts)
                await inventory.confirm_stocktake(session, keeper_id, stocktake_id)
                await session.commit()
            assert await stock() == at_opening
            async with factory() as session:
                assert (await session.get(Stocktake, stocktake_id)).status == "Đã xác nhận"
        assert sum(outcomes.values()) == STOCKTAKE_ROUNDS
