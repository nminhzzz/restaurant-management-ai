"""add payment exceptions

Revision ID: 4f7a1c2d9e10
Revises: 2dbae7c74ed0
Create Date: 2026-10-20 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4f7a1c2d9e10"
down_revision: str | None = "2dbae7c74ed0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "NGOAI_LE_THANH_TOAN",
        sa.Column("MaNgoaiLe", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("MaGiaoDichTT", sa.BigInteger(), nullable=True),
        sa.Column("MaOrder", sa.BigInteger(), nullable=True),
        sa.Column("MaGiaoDichCong", sa.String(100), nullable=False),
        sa.Column("SoTien", sa.DECIMAL(18, 4), nullable=False),
        sa.Column("TrangThai", sa.String(30), nullable=False, server_default="Chờ xử lý"),
        sa.Column("LyDo", sa.String(255), nullable=True),
        sa.Column("GhiChu", sa.String(255), nullable=True),
        sa.Column("BusinessDate", sa.Date(), nullable=False),
        sa.Column("NgayTao", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("ThoiDiemXuLy", sa.DateTime(), nullable=True),
        sa.Column("NguoiXuLy", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["MaGiaoDichTT"],
            ["GIAO_DICH_THANH_TOAN.MaGiaoDichTT"],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaOrder"], ["ORDER.MaOrder"], ondelete="RESTRICT", onupdate="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["NguoiXuLy"], ["NGUOI_DUNG.MaNguoiDung"], ondelete="RESTRICT", onupdate="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("MaNgoaiLe"),
        sa.UniqueConstraint("MaGiaoDichCong"),
    )
    op.create_index("ix_NGOAI_LE_THANH_TOAN_TrangThai", "NGOAI_LE_THANH_TOAN", ["TrangThai"])
    op.create_index("ix_NGOAI_LE_THANH_TOAN_BusinessDate", "NGOAI_LE_THANH_TOAN", ["BusinessDate"])


def downgrade() -> None:
    op.drop_index("ix_NGOAI_LE_THANH_TOAN_BusinessDate", table_name="NGOAI_LE_THANH_TOAN")
    op.drop_index("ix_NGOAI_LE_THANH_TOAN_TrangThai", table_name="NGOAI_LE_THANH_TOAN")
    op.drop_table("NGOAI_LE_THANH_TOAN")
