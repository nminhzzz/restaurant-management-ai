"""Exercise cutoff-history migration against an isolated SQLite database."""

import importlib.util
from datetime import date, time
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_upgrade_preserves_initial_cutoff_and_downgrade_removes_history():
    path = (
        Path(__file__).parents[2]
        / "migrations/versions"
        / "d23102300001_business_date_cutoff_history.py"
    )
    spec = importlib.util.spec_from_file_location("cutoff_migration", path)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine("sqlite://")
    metadata = sa.MetaData()
    config = sa.Table(
        "CAU_HINH_HE_THONG", metadata, sa.Column("GioBatDauBusinessDate", sa.Time(), nullable=False)
    )
    with engine.begin() as connection:
        metadata.create_all(connection)
        connection.execute(config.insert().values(GioBatDauBusinessDate=time(7, 45)))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            table = sa.Table("LICH_GIO_BUSINESS_DATE", sa.MetaData(), autoload_with=connection)
            row = connection.execute(sa.select(table)).one()
            assert row.NgayHieuLuc == date(1000, 1, 1)
            assert row.GioBatDau == time(7, 45)
            assert row.ThoiDiemBatDau.time() == time(7, 45)
            migration.downgrade()
        assert not sa.inspect(connection).has_table("LICH_GIO_BUSINESS_DATE")
    engine.dispose()
