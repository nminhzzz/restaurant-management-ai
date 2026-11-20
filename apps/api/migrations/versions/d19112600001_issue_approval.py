"""A system-proposed write-off waits for approval (supervisor review 2026-11-19).

The system proposes a voucher for expired lots in 'Chờ duyệt'; it moves no stock until a
manager or the kitchen approves it ('Đã xác nhận') or rejects it ('Đã từ chối'). The voucher
keeps who decided and when, and each proposed line keeps the lot it will draw.

Revision ID: d19112600001
Revises: d13112600001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "d19112600001"
down_revision: str | None = "d13112600001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("PHIEU_XUAT_KHO", sa.Column("NguoiDuyet", sa.BigInteger(), nullable=True))
    op.add_column("PHIEU_XUAT_KHO", sa.Column("NgayDuyet", mysql.DATETIME(fsp=3), nullable=True))
    op.create_foreign_key(
        "fk_PHIEU_XUAT_KHO_NguoiDuyet",
        "PHIEU_XUAT_KHO",
        "NGUOI_DUNG",
        ["NguoiDuyet"],
        ["MaNguoiDung"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.add_column(
        "CHI_TIET_PHIEU_XUAT", sa.Column("MaLoNguyenLieu", sa.BigInteger(), nullable=True)
    )
    op.create_foreign_key(
        "fk_CHI_TIET_PHIEU_XUAT_MaLoNguyenLieu",
        "CHI_TIET_PHIEU_XUAT",
        "LO_NGUYEN_LIEU",
        ["MaLoNguyenLieu"],
        ["MaLoNguyenLieu"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def downgrade() -> None:
    # Vouchers already in 'Chờ duyệt' / 'Đã từ chối' keep those statuses: this only drops the
    # columns, so it is a development rollback, not a production one.
    op.drop_constraint(
        "fk_CHI_TIET_PHIEU_XUAT_MaLoNguyenLieu", "CHI_TIET_PHIEU_XUAT", type_="foreignkey"
    )
    op.drop_column("CHI_TIET_PHIEU_XUAT", "MaLoNguyenLieu")
    op.drop_constraint("fk_PHIEU_XUAT_KHO_NguoiDuyet", "PHIEU_XUAT_KHO", type_="foreignkey")
    op.drop_column("PHIEU_XUAT_KHO", "NgayDuyet")
    op.drop_column("PHIEU_XUAT_KHO", "NguoiDuyet")
