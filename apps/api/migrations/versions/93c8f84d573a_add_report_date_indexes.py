"""add report date indexes

Revision ID: 93c8f84d573a
Revises: 8891574f0e84
Create Date: 2026-10-18 17:54:13.744644
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "93c8f84d573a"
down_revision: str | None = "8891574f0e84"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_ORDER_BusinessDate_TrangThai", "ORDER", ["BusinessDate", "TrangThai"])
    op.create_index(
        "ix_CHI_TIET_ORDER_MaOrder_TrangThai",
        "CHI_TIET_ORDER",
        ["MaOrder", "TrangThai"],
    )
    op.create_index(
        "ix_GIAO_DICH_THANH_TOAN_BusinessDate_TrangThai",
        "GIAO_DICH_THANH_TOAN",
        ["BusinessDate", "TrangThai"],
    )
    op.create_index("ix_HOA_DON_BusinessDate", "HOA_DON", ["BusinessDate"])
    op.create_index(
        "ix_GIAO_DICH_KHO_BusinessDate_LoaiGiaoDich",
        "GIAO_DICH_KHO",
        ["BusinessDate", "LoaiGiaoDich"],
    )


def downgrade() -> None:
    op.drop_index("ix_GIAO_DICH_KHO_BusinessDate_LoaiGiaoDich", table_name="GIAO_DICH_KHO")
    op.drop_index("ix_HOA_DON_BusinessDate", table_name="HOA_DON")
    op.drop_index(
        "ix_GIAO_DICH_THANH_TOAN_BusinessDate_TrangThai",
        table_name="GIAO_DICH_THANH_TOAN",
    )
    op.drop_index("ix_CHI_TIET_ORDER_MaOrder_TrangThai", table_name="CHI_TIET_ORDER")
    op.drop_index("ix_ORDER_BusinessDate_TrangThai", table_name="ORDER")
