"""link stocktake write-off issues

Revision ID: 2dbae7c74ed0
Revises: f8db86d6d0a4
Create Date: 2026-10-18 18:03:17.181348
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2dbae7c74ed0"
down_revision: str | None = "f8db86d6d0a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "PHIEU_XUAT_KHO",
        sa.Column("MaPhieuKiemKe", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_PHIEU_XUAT_KHO_MaPhieuKiemKe",
        "PHIEU_XUAT_KHO",
        "PHIEU_KIEM_KE",
        ["MaPhieuKiemKe"],
        ["MaPhieuKiemKe"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.create_index(
        "ix_PHIEU_XUAT_KHO_MaPhieuKiemKe",
        "PHIEU_XUAT_KHO",
        ["MaPhieuKiemKe"],
    )


def downgrade() -> None:
    op.drop_index("ix_PHIEU_XUAT_KHO_MaPhieuKiemKe", table_name="PHIEU_XUAT_KHO")
    op.drop_constraint("fk_PHIEU_XUAT_KHO_MaPhieuKiemKe", "PHIEU_XUAT_KHO", type_="foreignkey")
    op.drop_column("PHIEU_XUAT_KHO", "MaPhieuKiemKe")
