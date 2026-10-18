"""Exercise legacy occupancy reconciliation against real MySQL temporary tables."""

import importlib
import os

import pytest
import sqlalchemy as sa

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_migration_recovers_legacy_free_tables_and_rejects_ambiguity(mysql_engine_factory):
    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("MYSQL_TEST_DATABASE_URL is required")
    engine = mysql_engine_factory(url)
    migration = importlib.import_module(
        "migrations.versions.e31f52a6c901_table_occupancy_and_ai_runtime"
    )
    metadata = sa.MetaData()
    tables = sa.Table(
        "TEST_OCCUPANCY_TABLE",
        metadata,
        sa.Column("MaBan", sa.Integer(), primary_key=True),
        sa.Column("TrangThai", sa.String(20)),
        sa.Column("DaXoa", sa.Boolean()),
        sa.Column("MaOrderDangPhucVu", sa.Integer()),
        prefixes=["TEMPORARY"],
    )
    orders = sa.Table(
        "TEST_OCCUPANCY_ORDER",
        metadata,
        sa.Column("MaOrder", sa.Integer(), primary_key=True),
        sa.Column("MaBan", sa.Integer()),
        sa.Column("TrangThai", sa.String(20)),
        prefixes=["TEMPORARY"],
    )
    try:
        async with engine.connect() as conn:
            await conn.run_sync(metadata.create_all)
            try:
                await conn.execute(
                    tables.insert(),
                    [
                        {"MaBan": 1, "TrangThai": "Trống", "DaXoa": False},
                        {"MaBan": 2, "TrangThai": "Đang phục vụ", "DaXoa": False},
                        {"MaBan": 3, "TrangThai": "Trống", "DaXoa": False},
                        {"MaBan": 4, "TrangThai": "Đang phục vụ", "DaXoa": False},
                    ],
                )
                await conn.execute(
                    orders.insert(),
                    [
                        {"MaOrder": 10, "MaBan": 1, "TrangThai": "Đang mở"},
                        {"MaOrder": 20, "MaBan": 2, "TrangThai": "Chờ đối soát"},
                        {"MaOrder": 30, "MaBan": 3, "TrangThai": "Đã thanh toán"},
                        {"MaOrder": 40, "MaBan": 4, "TrangThai": "Đang mở"},
                        {"MaOrder": 41, "MaBan": 4, "TrangThai": "Đã thanh toán"},
                    ],
                )
                await conn.run_sync(
                    lambda sync: migration.assert_unambiguous_occupancy(sync, tables, orders)
                )
                await conn.run_sync(lambda sync: migration.backfill_occupancy(sync, tables, orders))
                rows = (await conn.execute(sa.select(tables).order_by(tables.c.MaBan))).all()
                assert [(r.TrangThai, r.MaOrderDangPhucVu) for r in rows] == [
                    ("Đang phục vụ", 10),
                    ("Đang phục vụ", 20),
                    ("Trống", None),
                    ("Đang phục vụ", 40),
                ]
                await conn.execute(
                    orders.insert(), {"MaOrder": 11, "MaBan": 1, "TrangThai": "Đang mở"}
                )
                with pytest.raises(RuntimeError, match="Multiple open orders"):
                    await conn.run_sync(
                        lambda sync: migration.assert_unambiguous_occupancy(sync, tables, orders)
                    )
            finally:
                await conn.exec_driver_sql("DROP TEMPORARY TABLE IF EXISTS TEST_OCCUPANCY_ORDER")
                await conn.exec_driver_sql("DROP TEMPORARY TABLE IF EXISTS TEST_OCCUPANCY_TABLE")
                await conn.rollback()
    finally:
        await engine.dispose()
