"""MySQL row-lock behavior for stocktake versus stock-changing transactions."""

import asyncio

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.errors import BusinessRuleError
from app.modules.inventory.models import Stocktake
from app.modules.inventory.stock import StockChange, apply_stock_movement, lock_stocktake_gate
from app.modules.settings.models import SystemConfig
from app.shared.enums import StocktakeStatus


@pytest.mark.anyio
@pytest.mark.integration
async def test_stocktake_gate_waits_then_observes_commit_and_rollback(mysql_engine_factory):
    engine = mysql_engine_factory()
    try:
        async with engine.connect() as connection:
            version = str((await connection.execute(text("SELECT VERSION()"))).scalar_one())
            if not version.startswith("8.4"):
                pytest.skip(f"MySQL 8.4 required; found {version}")
            config_id = (await connection.execute(select(SystemConfig.id))).scalar_one_or_none()
            if config_id is None:
                pytest.skip("Seeded config row required")
            active = (
                await connection.execute(
                    select(Stocktake.id).where(
                        Stocktake.status == StocktakeStatus.DANG_KIEM_KE.value
                    )
                )
            ).scalar_one_or_none()
            if active is not None:
                pytest.skip("Database already has an active stocktake")
    except OperationalError as exc:
        pytest.skip(f"MySQL unavailable: {type(exc).__name__}")

    factory = async_sessionmaker(engine, expire_on_commit=False)
    created_id = None
    try:
        async with factory() as creator, factory() as contender:
            await lock_stocktake_gate(creator, allow_active=True)
            stocktake = Stocktake(status=StocktakeStatus.DANG_KIEM_KE.value)
            creator.add(stocktake)
            await creator.flush()
            created_id = stocktake.id
            # Auth/read dependencies can establish a REPEATABLE READ snapshot
            # before the service acquires its current-read row lock.
            await contender.execute(select(SystemConfig.restaurant_name))
            competing_check = asyncio.create_task(
                apply_stock_movement(contender, StockChange(ingredient_id=-1, delta=-1))
            )
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(competing_check), timeout=0.1)
            await creator.commit()
            with pytest.raises(BusinessRuleError, match="Đang kiểm kê"):
                await asyncio.wait_for(competing_check, timeout=2)
            await contender.rollback()

        async with factory() as cleanup:
            row = await cleanup.get(Stocktake, created_id)
            assert row is not None
            await cleanup.delete(row)
            await cleanup.commit()
        created_id = None

        async with factory() as creator, factory() as contender:
            await lock_stocktake_gate(creator, allow_active=True)
            rolled_back = Stocktake(status=StocktakeStatus.DANG_KIEM_KE.value)
            creator.add(rolled_back)
            await creator.flush()
            rolled_back_id = rolled_back.id
            competing_check = asyncio.create_task(
                apply_stock_movement(contender, StockChange(ingredient_id=-1, delta=-1))
            )
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(competing_check), timeout=0.1)
            await creator.rollback()
            with pytest.raises(BusinessRuleError, match="Nguyên liệu không tồn tại"):
                await asyncio.wait_for(competing_check, timeout=2)
            await contender.rollback()
        async with factory() as verify:
            assert await verify.get(Stocktake, rolled_back_id) is None
    finally:
        if created_id is not None:
            async with factory() as cleanup:
                row = await cleanup.get(Stocktake, created_id)
                if row is not None:
                    await cleanup.delete(row)
                    await cleanup.commit()
        await engine.dispose()
