-- One row per topic record; no joins to other one-to-many topics.
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
  ON o.MaOrder = ct.MaOrder;
