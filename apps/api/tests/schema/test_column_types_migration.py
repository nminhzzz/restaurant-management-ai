"""Narrowing a money column must never silently drop digits (report §4.2.2)."""

import importlib
import os

import pytest
import sqlalchemy as sa

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_a_money_column_with_extra_decimals_blocks_the_migration(mysql_engine_factory):
    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("MYSQL_TEST_DATABASE_URL is required")
    migration = importlib.import_module("migrations.versions.d01112600005_column_types")
    engine = mysql_engine_factory(url)
    metadata = sa.MetaData()
    table = sa.Table(
        "TEST_MONEY_NARROWING",
        metadata,
        sa.Column("Id", sa.Integer(), primary_key=True),
        sa.Column("SoTien", sa.DECIMAL(18, 4)),
        prefixes=["TEMPORARY"],
    )
    try:
        async with engine.connect() as conn:
            await conn.run_sync(metadata.create_all)
            try:
                await conn.execute(table.insert(), [{"Id": 1, "SoTien": "1200.5000"}])
                await conn.run_sync(
                    lambda sync: migration._assert_no_precision_loss(
                        sync, "TEST_MONEY_NARROWING", "SoTien", 2
                    )
                )
                await conn.execute(table.insert(), [{"Id": 2, "SoTien": "10.1234"}])
                with pytest.raises(RuntimeError, match="SoTien"):
                    await conn.run_sync(
                        lambda sync: migration._assert_no_precision_loss(
                            sync, "TEST_MONEY_NARROWING", "SoTien", 2
                        )
                    )
            finally:
                await conn.run_sync(metadata.drop_all)
    finally:
        await engine.dispose()
