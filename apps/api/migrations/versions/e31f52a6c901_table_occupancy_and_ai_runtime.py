"""Separate physical table occupancy and persist shared AI runtime state."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e31f52a6c901"
down_revision: str | None = "b7c9d3e1f420"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def assert_unambiguous_occupancy(connection, tables, orders) -> None:
    ambiguous = (
        connection.execute(
            sa.select(tables.c.MaBan)
            .join(orders, orders.c.MaBan == tables.c.MaBan)
            .where(tables.c.DaXoa.is_(False), orders.c.TrangThai == "Đang mở")
            .group_by(tables.c.MaBan)
            .having(sa.func.count() > 1)
        )
        .scalars()
        .all()
    )
    if ambiguous:
        raise RuntimeError(
            f"Multiple open orders occupy tables {ambiguous}; reconcile them before migration"
        )


def backfill_occupancy(connection, tables, orders) -> None:
    open_orders = connection.execute(
        sa.select(orders.c.MaBan, sa.func.max(orders.c.MaOrder))
        .where(orders.c.TrangThai == "Đang mở", orders.c.MaBan.is_not(None))
        .group_by(orders.c.MaBan)
    ).all()
    for table_id, order_id in open_orders:
        connection.execute(
            sa.update(tables)
            .where(tables.c.DaXoa.is_(False), tables.c.MaBan == table_id)
            .values(MaOrderDangPhucVu=order_id, TrangThai="Đang phục vụ")
        )
    latest_order = (
        sa.select(sa.func.max(orders.c.MaOrder))
        .where(orders.c.MaBan == tables.c.MaBan)
        .correlate(tables)
        .scalar_subquery()
    )
    connection.execute(
        sa.update(tables)
        .where(tables.c.TrangThai == "Đang phục vụ", tables.c.MaOrderDangPhucVu.is_(None))
        .values(MaOrderDangPhucVu=latest_order)
    )


def upgrade() -> None:
    tables = sa.table(
        "BAN",
        sa.column("MaBan"),
        sa.column("TrangThai"),
        sa.column("DaXoa"),
        sa.column("MaOrderDangPhucVu"),
    )
    orders = sa.table("ORDER", sa.column("MaOrder"), sa.column("MaBan"), sa.column("TrangThai"))
    # Preflight before MySQL's nontransactional DDL, so ambiguity leaves no partial schema.
    assert_unambiguous_occupancy(op.get_bind(), tables, orders)
    op.add_column("BAN", sa.Column("MaOrderDangPhucVu", sa.BigInteger(), nullable=True))
    backfill_occupancy(op.get_bind(), tables, orders)
    op.create_unique_constraint("uq_BAN_MaOrderDangPhucVu", "BAN", ["MaOrderDangPhucVu"])
    op.create_foreign_key(
        "fk_BAN_MaOrderDangPhucVu_ORDER",
        "BAN",
        "ORDER",
        ["MaOrderDangPhucVu"],
        ["MaOrder"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    # Technical tables are outside the restaurant domain diagram and AI views.
    op.create_table(
        "HAN_MUC_AI_NGAY",
        sa.Column("BusinessDate", sa.Date(), primary_key=True),
        sa.Column("SoLanGoi", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("SoLanGoi >= 0", name=op.f("ck_HAN_MUC_AI_NGAY_nonnegative_calls")),
    )
    op.create_table(
        "BO_NHO_DEM_SQL_AI",
        sa.Column("KhoaCache", sa.String(64), primary_key=True),
        sa.Column("CauSQL", sa.Text(), nullable=False),
        sa.Column("HetHanLuc", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_BO_NHO_DEM_SQL_AI_HetHanLuc", "BO_NHO_DEM_SQL_AI", ["HetHanLuc"])


def downgrade() -> None:
    op.drop_table("BO_NHO_DEM_SQL_AI")
    op.drop_table("HAN_MUC_AI_NGAY")
    op.drop_constraint("fk_BAN_MaOrderDangPhucVu_ORDER", "BAN", type_="foreignkey")
    op.drop_constraint("uq_BAN_MaOrderDangPhucVu", "BAN", type_="unique")
    op.drop_column("BAN", "MaOrderDangPhucVu")
