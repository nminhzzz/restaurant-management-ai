-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_dongmon AS
SELECT
  'DONG_MON' AS LoaiBanGhi,
  ct.MaOrder AS MaOrder,
  o.BusinessDate AS BusinessDate,
  o.TrangThai AS TrangThaiOrder,
  m.TenMon AS TenMon,
  ng.TenNhomMon AS TenNhom,
  ct.SoLuong AS SoLuongMon,
  ct.DonGia AS DonGiaMon,
  (
    ct.SoLuong * ct.DonGia
  ) AS ThanhTienMon
FROM CHI_TIET_ORDER AS ct
JOIN `ORDER` AS o
  ON o.MaOrder = ct.MaOrder
JOIN MON_AN AS m
  ON m.MaMon = ct.MaMon
LEFT JOIN NHOM_MON AS ng
  ON ng.MaNhomMon = m.MaNhomMon
WHERE
  ct.TrangThai <> 'Đã hủy';
