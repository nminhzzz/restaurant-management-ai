"""add ingredient reservations

Revision ID: eacd6036a5ab
Revises: 0fee63547c48
Create Date: 2026-10-18 16:07:40.598139
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "eacd6036a5ab"
down_revision: str | None = "0fee63547c48"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "GIU_CHO_MON",
        sa.Column("MaGiuCho", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("MaLuotChon", sa.String(36), nullable=False),
        sa.Column("MaNguoiDung", sa.BigInteger(), nullable=False),
        sa.Column("MaBan", sa.BigInteger(), nullable=True),
        sa.Column("MaOrder", sa.BigInteger(), nullable=True),
        sa.Column("MaMon", sa.BigInteger(), nullable=False),
        sa.Column("MaCongThuc", sa.BigInteger(), nullable=True),
        sa.Column("MaPhienBanGia", sa.BigInteger(), nullable=True),
        sa.Column("SoLuong", sa.Integer(), nullable=False),
        sa.Column("GhiChu", sa.String(500), nullable=True),
        sa.Column("ThoiDiemHetHan", sa.DateTime(), nullable=False),
        sa.Column("TrangThai", sa.String(20), nullable=False, server_default="Đang giữ"),
        sa.Column("MaYeuCauGui", sa.String(36), nullable=True),
        sa.Column("MaDongYeuCau", sa.String(36), nullable=True),
        sa.Column("MaChiTietOrder", sa.BigInteger(), nullable=True),
        sa.Column("NgayTao", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("SoLuong > 0", name="ck_GIU_CHO_MON_positive_quantity"),
        sa.ForeignKeyConstraint(
            ["MaNguoiDung"], ["NGUOI_DUNG.MaNguoiDung"], name="fk_GIU_CHO_MON_MaNguoiDung"
        ),
        sa.ForeignKeyConstraint(["MaBan"], ["BAN.MaBan"], name="fk_GIU_CHO_MON_MaBan"),
        sa.ForeignKeyConstraint(["MaOrder"], ["ORDER.MaOrder"], name="fk_GIU_CHO_MON_MaOrder"),
        sa.ForeignKeyConstraint(["MaMon"], ["MON_AN.MaMon"], name="fk_GIU_CHO_MON_MaMon"),
        sa.ForeignKeyConstraint(
            ["MaCongThuc"], ["CONG_THUC.MaCongThuc"], name="fk_GIU_CHO_MON_MaCongThuc"
        ),
        sa.ForeignKeyConstraint(
            ["MaPhienBanGia"],
            ["LICH_SU_GIA_MON.MaPhienBanGia"],
            name="fk_GIU_CHO_MON_MaPhienBanGia",
        ),
        sa.ForeignKeyConstraint(
            ["MaChiTietOrder"],
            ["CHI_TIET_ORDER.MaChiTietOrder"],
            name="fk_GIU_CHO_MON_MaChiTietOrder",
        ),
        sa.PrimaryKeyConstraint("MaGiuCho", name="pk_GIU_CHO_MON"),
        sa.UniqueConstraint("MaChiTietOrder", name="uq_GIU_CHO_MON_MaChiTietOrder"),
        sa.UniqueConstraint("MaYeuCauGui", "MaDongYeuCau", name="uq_GIU_CHO_MON_request_line"),
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
        sa.CheckConstraint("SoLuongGiu > 0", name="ck_CHI_TIET_GIU_CHO_positive_quantity"),
        sa.ForeignKeyConstraint(
            ["MaGiuCho"],
            ["GIU_CHO_MON.MaGiuCho"],
            name="fk_CHI_TIET_GIU_CHO_MaGiuCho",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["MaLoNguyenLieu"],
            ["LO_NGUYEN_LIEU.MaLoNguyenLieu"],
            name="fk_CHI_TIET_GIU_CHO_MaLoNguyenLieu",
        ),
        sa.PrimaryKeyConstraint("MaGiuCho", "MaLoNguyenLieu", name="pk_CHI_TIET_GIU_CHO"),
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
