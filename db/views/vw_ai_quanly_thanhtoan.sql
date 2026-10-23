-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_thanhtoan AS
SELECT
  'THANH_TOAN' AS LoaiBanGhi,
  t.MaOrder AS MaOrder,
  t.BusinessDate AS BusinessDate,
  t.MaGiaoDichTT AS MaGiaoDich,
  t.PhuongThuc AS PhuongThuc,
  t.SoTien AS SoTien
FROM GIAO_DICH_THANH_TOAN AS t
WHERE
  t.TrangThai = 'Thành công';
