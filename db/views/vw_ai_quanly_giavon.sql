-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_giavon AS
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
  ON n.MaNguyenLieu = gv.MaNguyenLieu;
