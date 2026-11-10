"""Moving weighted average costing (handoff 2026-11-08 A1, document 04 F.27 and G.1).

* GIAO_DICH_KHO.GiaTri: the value of a movement, written once when it happens. NULL while the
  ingredient has never been priced.
* LICH_SU_GIA_BINH_QUAN: one row per recalculation of an ingredient's unit cost.
* GIA_BINH_QUAN_THANG is dropped together with the monthly method. Its rows are not carried
  over: development and demo data are regenerated, and a monthly average says nothing about the
  unit cost in force at a given moment.
* vw_ai_quanly_giavon now reads the history table instead of the monthly one.

Movements written before this migration keep GiaTri NULL: the unit cost they left at was never
recorded. Downgrade restores the empty monthly table and the previous view.

Revision ID: d08112600001
Revises: d06112600001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision: str = "d08112600001"
down_revision: str | None = "d06112600001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DATETIME3 = sa.DateTime().with_variant(mysql.DATETIME(fsp=3), "mysql")

NEW_VIEW = """CREATE OR REPLACE VIEW vw_ai_quanly_giavon AS
SELECT
  'LICH_SU_GIA' AS LoaiBanGhi,
  gv.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  gv.ThoiDiemHieuLuc AS ThoiDiemHieuLuc,
  gv.DonGiaBinhQuan AS DonGiaBinhQuan,
  gv.SoLuongTon AS SoLuongTon
FROM LICH_SU_GIA_BINH_QUAN AS gv
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = gv.MaNguyenLieu"""

OLD_VIEW = """CREATE OR REPLACE VIEW vw_ai_quanly_giavon AS
SELECT
  'GIA_VON_THANG' AS LoaiBanGhi,
  gv.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  gv.Thang AS Thang,
  gv.DonGiaBinhQuan AS GiaBinhQuanThang,
  gv.TongSoLuongNhap AS TongSoLuongNhapThang
FROM GIA_BINH_QUAN_THANG AS gv
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = gv.MaNguyenLieu"""


def upgrade() -> None:
    op.add_column("GIAO_DICH_KHO", sa.Column("GiaTri", sa.DECIMAL(18, 2), nullable=True))
    op.create_table(
        "LICH_SU_GIA_BINH_QUAN",
        sa.Column("MaNguyenLieu", sa.BigInteger(), nullable=False),
        sa.Column("ThoiDiemHieuLuc", DATETIME3, nullable=False),
        sa.Column("DonGiaBinhQuan", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("SoLuongTon", sa.DECIMAL(18, 6), nullable=False),
        sa.Column("MaGiaoDichKho", sa.BigInteger(), nullable=True),
        sa.ForeignKeyConstraint(
            ["MaNguyenLieu"],
            ["NGUYEN_LIEU.MaNguyenLieu"],
            name=op.f("fk_LICH_SU_GIA_BINH_QUAN_MaNguyenLieu"),
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["MaGiaoDichKho"],
            ["GIAO_DICH_KHO.MaGiaoDichKho"],
            name=op.f("fk_LICH_SU_GIA_BINH_QUAN_MaGiaoDichKho"),
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "MaNguyenLieu", "ThoiDiemHieuLuc", name=op.f("pk_LICH_SU_GIA_BINH_QUAN")
        ),
    )
    op.execute(NEW_VIEW)
    op.drop_table("GIA_BINH_QUAN_THANG")


def downgrade() -> None:
    op.create_table(
        "GIA_BINH_QUAN_THANG",
        sa.Column("MaNguyenLieu", sa.BigInteger(), nullable=False),
        sa.Column("Thang", sa.Integer(), nullable=False),
        sa.Column("DonGiaBinhQuan", sa.DECIMAL(18, 2), nullable=False),
        sa.Column("TongSoLuongNhap", sa.DECIMAL(18, 6), nullable=False),
        sa.Column(
            "ThoiDiemTinh",
            DATETIME3,
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(3)"),
        ),
        sa.ForeignKeyConstraint(
            ["MaNguyenLieu"],
            ["NGUYEN_LIEU.MaNguyenLieu"],
            name=op.f("fk_GIA_BINH_QUAN_THANG_MaNguyenLieu"),
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("MaNguyenLieu", "Thang", name=op.f("pk_GIA_BINH_QUAN_THANG")),
    )
    op.execute(OLD_VIEW)
    op.drop_table("LICH_SU_GIA_BINH_QUAN")
    op.drop_column("GIAO_DICH_KHO", "GiaTri")
