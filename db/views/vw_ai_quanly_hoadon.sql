-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_hoadon AS
SELECT
  'HOA_DON' AS LoaiBanGhi,
  h.MaOrder AS MaOrder,
  h.BusinessDate AS BusinessDate,
  h.MaHoaDon AS MaHoaDon,
  h.ThoiDiemXuat AS ThoiDiemXuat,
  h.TongTien AS TongTien
FROM HOA_DON AS h;
