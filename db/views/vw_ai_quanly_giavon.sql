-- One row per recalculation of an ingredient's moving weighted average unit cost.
CREATE OR REPLACE VIEW vw_ai_quanly_giavon AS
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
  ON n.MaNguyenLieu = gv.MaNguyenLieu;
