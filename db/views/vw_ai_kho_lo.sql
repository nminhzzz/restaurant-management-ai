-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_kho_lo AS
SELECT
  'LO_NGUYEN_LIEU' AS LoaiBanGhi,
  l.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  l.MaLoNguyenLieu AS MaLo,
  l.SoLuongConLai AS SoLuongConLai,
  l.TrangThai AS TrangThaiLo,
  l.NgayNhap AS NgayNhapLo,
  l.HanSuDung AS HanSuDungLo
FROM LO_NGUYEN_LIEU AS l
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = l.MaNguyenLieu;
