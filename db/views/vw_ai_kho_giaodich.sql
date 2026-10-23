-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_kho_giaodich AS
SELECT
  'GIAO_DICH_KHO' AS LoaiBanGhi,
  g.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  g.MaGiaoDichKho AS MaGiaoDichKho,
  g.BusinessDate AS BusinessDate,
  g.SoLuongThayDoi AS SoLuong,
  g.LoaiGiaoDich AS LoaiGiaoDich
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu;
