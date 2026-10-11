"""Add effective Business Date and runtime system settings.

Revision ID: 8a6e2b1c4d30
Revises: b7c9d3e1f420
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8a6e2b1c4d30"
down_revision: str | None = "b7c9d3e1f420"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "CAU_HINH_HE_THONG", sa.Column("GioBatDauBusinessDateMoi", sa.Time(), nullable=True)
    )
    op.add_column("CAU_HINH_HE_THONG", sa.Column("NgayHieuLucGioMoi", sa.Date(), nullable=True))
    op.add_column(
        "CAU_HINH_HE_THONG",
        sa.Column("SoNgayCanhBaoHetHan", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "CAU_HINH_HE_THONG",
        sa.Column("SoCauHoiAIMoiNgay", sa.Integer(), nullable=False, server_default="50"),
    )
    op.add_column(
        "CAU_HINH_HE_THONG",
        sa.Column("ThoiGianGiuChoPhut", sa.Integer(), nullable=False, server_default="5"),
    )


def downgrade() -> None:
    op.drop_column("CAU_HINH_HE_THONG", "ThoiGianGiuChoPhut")
    op.drop_column("CAU_HINH_HE_THONG", "SoCauHoiAIMoiNgay")
    op.drop_column("CAU_HINH_HE_THONG", "SoNgayCanhBaoHetHan")
    op.drop_column("CAU_HINH_HE_THONG", "NgayHieuLucGioMoi")
    op.drop_column("CAU_HINH_HE_THONG", "GioBatDauBusinessDateMoi")
