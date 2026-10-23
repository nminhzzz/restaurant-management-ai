-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_nhap AS
SELECT
  'PHIEU_NHAP' AS LoaiBanGhi,
  CASE WHEN pn.NgayNhap < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(pn.NgayNhap)), TIMESTAMP(DATE(pn.NgayNhap), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(pn.NgayNhap) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(pn.NgayNhap), INTERVAL 1 DAY) ELSE DATE(pn.NgayNhap) END AS BusinessDate,
  ct.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  pn.MaPhieuNhap AS MaPhieuNhap,
  ncc.TenNCC AS TenNhaCungCap,
  ct.DonGia AS DonGiaNhap,
  ct.SoLuong AS SoLuongNhap
FROM CHI_TIET_PHIEU_NHAP AS ct
JOIN PHIEU_NHAP_KHO AS pn
  ON pn.MaPhieuNhap = ct.MaPhieuNhap
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = ct.MaNguyenLieu
LEFT JOIN NHA_CUNG_CAP AS ncc
  ON ncc.MaNCC = pn.MaNCC
WHERE
  pn.TrangThai <> 'Đã hủy';
