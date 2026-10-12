"""Add server-side item holds and held ingredient lots.

Revision ID: d2f8a7c4e901
Revises: 8a6e2b1c4d30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2f8a7c4e901"
down_revision: str | None = "8a6e2b1c4d30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "GIU_CHO_MON",
        sa.Column("MaGiuCho", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("MaLuotChon", sa.String(64), nullable=False),
        sa.Column("MaNguoiDung", sa.BigInteger(), nullable=False),
        sa.Column("MaBan", sa.BigInteger(), nullable=True),
        sa.Column("MaOrder", sa.BigInteger(), nullable=True),
        sa.Column("MaMon", sa.BigInteger(), nullable=False),
        sa.Column("MaCongThuc", sa.BigInteger(), nullable=False),
        sa.Column("MaPhienBanGia", sa.BigInteger(), nullable=False),
        sa.Column("SoLuong", sa.Integer(), nullable=False),
        sa.Column("GhiChu", sa.String(500), nullable=True),
        sa.Column("ThoiDiemHetHan", sa.DateTime(), nullable=False),
        sa.Column("TrangThai", sa.String(20), nullable=False),
        sa.Column("MaYeuCauGui", sa.String(100), nullable=True),
        sa.Column("MaDongYeuCau", sa.String(100), nullable=True),
        sa.Column("MaChiTietOrder", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("MaGiuCho", name="pk_GIU_CHO_MON"),
        sa.ForeignKeyConstraint(
            ["MaNguoiDung"],
            ["NGUOI_DUNG.MaNguoiDung"],
            name="fk_GIU_CHO_MON_MaNguoiDung",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaBan"],
            ["BAN.MaBan"],
            name="fk_GIU_CHO_MON_MaBan",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaOrder"],
            ["ORDER.MaOrder"],
            name="fk_GIU_CHO_MON_MaOrder",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaMon"],
            ["MON_AN.MaMon"],
            name="fk_GIU_CHO_MON_MaMon",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaCongThuc"],
            ["CONG_THUC.MaCongThuc"],
            name="fk_GIU_CHO_MON_MaCongThuc",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaPhienBanGia"],
            ["LICH_SU_GIA_MON.MaPhienBanGia"],
            name="fk_GIU_CHO_MON_MaPhienBanGia",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaChiTietOrder"],
            ["CHI_TIET_ORDER.MaChiTietOrder"],
            name="fk_GIU_CHO_MON_MaChiTietOrder",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("SoLuong > 0", name="hold_quantity_positive"),
        sa.UniqueConstraint("MaChiTietOrder", name="uq_GIU_CHO_MON_MaChiTietOrder"),
        sa.UniqueConstraint(
            "MaYeuCauGui", "MaDongYeuCau", name="uq_GIU_CHO_MON_MaYeuCauGui_MaDongYeuCau"
        ),
    )
    op.create_index(
        "ix_GIU_CHO_MON_MaLuotChon_TrangThai", "GIU_CHO_MON", ["MaLuotChon", "TrangThai"]
    )
    op.create_index(
        "ix_GIU_CHO_MON_TrangThai_ThoiDiemHetHan",
        "GIU_CHO_MON",
        ["TrangThai", "ThoiDiemHetHan"],
    )

    op.create_table(
        "CHI_TIET_GIU_CHO",
        sa.Column("MaGiuCho", sa.BigInteger(), nullable=False),
        sa.Column("MaLoNguyenLieu", sa.BigInteger(), nullable=False),
        sa.Column("SoLuongGiu", sa.DECIMAL(18, 4), nullable=False),
        sa.PrimaryKeyConstraint("MaGiuCho", "MaLoNguyenLieu", name="pk_CHI_TIET_GIU_CHO"),
        sa.ForeignKeyConstraint(
            ["MaGiuCho"],
            ["GIU_CHO_MON.MaGiuCho"],
            name="fk_CHI_TIET_GIU_CHO_MaGiuCho",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaLoNguyenLieu"],
            ["LO_NGUYEN_LIEU.MaLoNguyenLieu"],
            name="fk_CHI_TIET_GIU_CHO_MaLoNguyenLieu",
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        ),
        sa.CheckConstraint("SoLuongGiu > 0", name="held_quantity_positive"),
    )
    op.create_index(
        "ix_CHI_TIET_GIU_CHO_MaLoNguyenLieu_MaGiuCho",
        "CHI_TIET_GIU_CHO",
        ["MaLoNguyenLieu", "MaGiuCho"],
    )


def downgrade() -> None:
    op.drop_index("ix_CHI_TIET_GIU_CHO_MaLoNguyenLieu_MaGiuCho", table_name="CHI_TIET_GIU_CHO")
    op.drop_table("CHI_TIET_GIU_CHO")
    op.drop_index("ix_GIU_CHO_MON_TrangThai_ThoiDiemHetHan", table_name="GIU_CHO_MON")
    op.drop_index("ix_GIU_CHO_MON_MaLuotChon_TrangThai", table_name="GIU_CHO_MON")
    op.drop_table("GIU_CHO_MON")
