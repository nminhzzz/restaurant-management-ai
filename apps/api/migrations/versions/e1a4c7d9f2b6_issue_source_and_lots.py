"""write-off source and lot/order-line references (FR-INV-05/06)

Revision ID: e1a4c7d9f2b6
Revises: d8f2b6c4e1a3
Create Date: 2026-10-21 23:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a4c7d9f2b6"
down_revision: str | None = "d8f2b6c4e1a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Report Bảng 37: a prepared-dish write-off points at the consumed order line
    # and the number of lost servings; the stock movement stays on the original draw.
    op.add_column(
        "CHI_TIET_PHIEU_XUAT", sa.Column("MaChiTietOrder", sa.BigInteger(), nullable=True)
    )
    op.add_column("CHI_TIET_PHIEU_XUAT", sa.Column("SoSuatHuy", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_CHI_TIET_PHIEU_XUAT_MaChiTietOrder",
        "CHI_TIET_PHIEU_XUAT",
        "CHI_TIET_ORDER",
        ["MaChiTietOrder"],
        ["MaChiTietOrder"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_check_constraint(
        "servings_positive_or_null",
        "CHI_TIET_PHIEU_XUAT",
        "SoSuatHuy IS NULL OR SoSuatHuy > 0",
    )


def downgrade() -> None:
    op.drop_constraint("servings_positive_or_null", "CHI_TIET_PHIEU_XUAT", type_="check")
    op.drop_constraint(
        "fk_CHI_TIET_PHIEU_XUAT_MaChiTietOrder", "CHI_TIET_PHIEU_XUAT", type_="foreignkey"
    )
    op.drop_column("CHI_TIET_PHIEU_XUAT", "SoSuatHuy")
    op.drop_column("CHI_TIET_PHIEU_XUAT", "MaChiTietOrder")
