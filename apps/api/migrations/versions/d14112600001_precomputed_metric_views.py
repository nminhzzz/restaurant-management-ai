"""Precomputed metric-group views for the assistant (v2, BA review 14/11/2026).

Hard questions timed out because the model reasoned its way through joins and CASE
expressions. These views carry the common analyses ready-made, by metric group rather than
by evaluation question: revenue per invoice with its table, order type and hour; revenue,
cost of goods and gross profit per business month; and the day's movements per ingredient.
The cashier gets revenue only; the warehouse gets quantities only. Grants are applied by
scripts/apply_grants.sh from db/views/grants.sql.template, as for the other topic views.

Revision ID: d14112600001
Revises: d13112600001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d14112600001"
down_revision: str | None = "d13112600001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

VIEWS = {
    "vw_ai_quanly_doanhthu": """-- One row per invoice with the order's table, order type and issue hour, so revenue by
-- table, order type, hour, day or month needs no join (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_quanly_doanhthu AS
SELECT
  h.MaHoaDon AS MaHoaDon,
  h.MaOrder AS MaOrder,
  h.BusinessDate AS BusinessDate,
  DATE_FORMAT(h.BusinessDate, '%Y-%m') AS Thang,
  HOUR(h.ThoiDiemXuat) AS Gio,
  o.MaBan AS MaBan,
  o.LoaiDon AS LoaiDon,
  h.TongTien AS DoanhThu
FROM HOA_DON AS h
JOIN `ORDER` AS o
  ON o.MaOrder = h.MaOrder""",
    "vw_ai_thungan_doanhthu": """-- One row per invoice with the order's table, order type and issue hour, so revenue by
-- table, order type, hour, day or month needs no join (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_thungan_doanhthu AS
SELECT
  h.MaHoaDon AS MaHoaDon,
  h.MaOrder AS MaOrder,
  h.BusinessDate AS BusinessDate,
  DATE_FORMAT(h.BusinessDate, '%Y-%m') AS Thang,
  HOUR(h.ThoiDiemXuat) AS Gio,
  o.MaBan AS MaBan,
  o.LoaiDon AS LoaiDon,
  h.TongTien AS DoanhThu
FROM HOA_DON AS h
JOIN `ORDER` AS o
  ON o.MaOrder = h.MaOrder""",
    "vw_ai_quanly_loinhuanthang": """-- One row per business month: revenue, cost of goods and gross profit (FR-REP-04 is a
-- monthly figure). Cost is -GiaTri of the ledger as written at the moving average: draws and
-- returns of finished orders, manual issues and stocktake adjustments; Hủy nhập is not cost
-- and an unvalued movement (GiaTri NULL) is left out, never counted as 0.
CREATE OR REPLACE VIEW vw_ai_quanly_loinhuanthang AS
SELECT
  k.Thang AS Thang,
  SUM(k.DoanhThu) AS DoanhThu,
  SUM(k.GiaVon) AS GiaVon,
  SUM(k.DoanhThu) - SUM(k.GiaVon) AS LoiNhuanGop,
  CASE
    WHEN SUM(k.DoanhThu) = 0 THEN NULL
    ELSE ROUND((SUM(k.DoanhThu) - SUM(k.GiaVon)) * 100 / SUM(k.DoanhThu), 2)
  END AS BienLoiNhuan
FROM (
  SELECT
    DATE_FORMAT(h.BusinessDate, '%Y-%m') AS Thang,
    h.TongTien AS DoanhThu,
    0 AS GiaVon
  FROM HOA_DON AS h
  UNION ALL
  SELECT
    DATE_FORMAT(g.BusinessDate, '%Y-%m') AS Thang,
    0 AS DoanhThu,
    -g.GiaTri AS GiaVon
  FROM GIAO_DICH_KHO AS g
  LEFT JOIN CHI_TIET_ORDER AS ct
    ON ct.MaChiTietOrder = g.MaChiTietOrder
  LEFT JOIN `ORDER` AS o
    ON o.MaOrder = ct.MaOrder
  WHERE
    NOT g.GiaTri IS NULL
    AND (
      (
        g.LoaiGiaoDich IN ('Trừ tự động', 'Hoàn kho')
        AND o.TrangThai IN ('Đã thanh toán', 'Đã hủy', 'Đóng \u2013 chưa thu được tiền')
      )
      OR g.LoaiGiaoDich IN ('Xuất thủ công', 'Điều chỉnh kiểm kê')
    )
) AS k
GROUP BY
  k.Thang""",
    "vw_ai_quanly_xuatnhapngay": """-- One row per business day and ingredient: every movement kind as its own positive
-- quantity (SoLuongDieuChinh keeps its sign), so intake, use and loss by period need no CASE
-- (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_quanly_xuatnhapngay AS
SELECT
  g.BusinessDate AS BusinessDate,
  g.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Nhập' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongNhap,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Hủy nhập' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongHuyNhap,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Trừ tự động' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongTieuHao,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Hoàn kho' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongHoanKho,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Xuất thủ công' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongXuatThuCong,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Điều chỉnh kiểm kê' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongDieuChinh,
  SUM(CASE WHEN NOT g.GiaTri IS NULL
    AND (
      (
        g.LoaiGiaoDich IN ('Trừ tự động', 'Hoàn kho')
        AND o.TrangThai IN ('Đã thanh toán', 'Đã hủy', 'Đóng \u2013 chưa thu được tiền')
      )
      OR g.LoaiGiaoDich IN ('Xuất thủ công', 'Điều chỉnh kiểm kê')
    ) THEN -g.GiaTri ELSE 0 END) AS GiaVon,
  SUM(CASE WHEN NOT g.GiaTri IS NULL
    AND (
      (
        g.LoaiGiaoDich IN ('Trừ tự động', 'Hoàn kho')
        AND o.TrangThai IN ('Đã thanh toán', 'Đã hủy', 'Đóng \u2013 chưa thu được tiền')
      )
      OR g.LoaiGiaoDich IN ('Xuất thủ công', 'Điều chỉnh kiểm kê')
    ) THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongGiaVon
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu
LEFT JOIN CHI_TIET_ORDER AS ct
  ON ct.MaChiTietOrder = g.MaChiTietOrder
LEFT JOIN `ORDER` AS o
  ON o.MaOrder = ct.MaOrder
GROUP BY
  g.BusinessDate,
  g.MaNguyenLieu,
  n.TenNguyenLieu,
  n.DonViTinh""",
    "vw_ai_kho_xuatnhapngay": """-- One row per business day and ingredient: every movement kind as its own positive
-- quantity (SoLuongDieuChinh keeps its sign), so intake, use and loss by period need no CASE
-- (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_kho_xuatnhapngay AS
SELECT
  g.BusinessDate AS BusinessDate,
  g.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Nhập' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongNhap,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Hủy nhập' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongHuyNhap,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Trừ tự động' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongTieuHao,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Hoàn kho' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongHoanKho,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Xuất thủ công' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongXuatThuCong,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Điều chỉnh kiểm kê' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongDieuChinh
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu
GROUP BY
  g.BusinessDate,
  g.MaNguyenLieu,
  n.TenNguyenLieu,
  n.DonViTinh""",
}


def upgrade() -> None:
    for sql in VIEWS.values():
        op.execute(sql)


def downgrade() -> None:
    for name in VIEWS:
        op.execute(f"DROP VIEW IF EXISTS {name}")
