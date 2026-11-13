"""vw_ai_quanly_giaodich exposes GIAO_DICH_KHO.GiaTri (handoff 2026-11-10 C1, FR-AI-02).

Only the manager's movement view gains the column; vw_ai_kho_giaodich and the cashier's views
are untouched, and no grant changes: the manager account already selects this view.

Revision ID: d12112600001
Revises: d08112600002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d12112600001"
down_revision: str | None = "d08112600002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_VIEW = """-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_giaodich AS
SELECT
  'GIAO_DICH_KHO' AS LoaiBanGhi,
  ct.MaOrder AS MaOrder,
  g.BusinessDate AS BusinessDate,
  o.TrangThai AS TrangThaiOrder,
  g.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  g.MaGiaoDichKho AS MaGiaoDichKho,
  g.SoLuongThayDoi AS SoLuong,
  g.LoaiGiaoDich AS LoaiGiaoDich,
  g.GiaTri AS GiaTri
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu
LEFT JOIN CHI_TIET_ORDER AS ct
  ON ct.MaChiTietOrder = g.MaChiTietOrder
LEFT JOIN `ORDER` AS o
  ON o.MaOrder = ct.MaOrder"""

OLD_VIEW = """-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_giaodich AS
SELECT
  'GIAO_DICH_KHO' AS LoaiBanGhi,
  ct.MaOrder AS MaOrder,
  g.BusinessDate AS BusinessDate,
  o.TrangThai AS TrangThaiOrder,
  g.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  g.MaGiaoDichKho AS MaGiaoDichKho,
  g.SoLuongThayDoi AS SoLuong,
  g.LoaiGiaoDich AS LoaiGiaoDich
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu
LEFT JOIN CHI_TIET_ORDER AS ct
  ON ct.MaChiTietOrder = g.MaChiTietOrder
LEFT JOIN `ORDER` AS o
  ON o.MaOrder = ct.MaOrder"""


def upgrade() -> None:
    op.execute(NEW_VIEW)


def downgrade() -> None:
    op.execute(OLD_VIEW)
