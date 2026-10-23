-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_kho_nhap AS
SELECT p.MaPhieuNhap, CASE WHEN p.NgayNhap < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(p.NgayNhap)), TIMESTAMP(DATE(p.NgayNhap), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(p.NgayNhap) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(p.NgayNhap), INTERVAL 1 DAY) ELSE DATE(p.NgayNhap) END AS BusinessDate,
p.TrangThai, ncc.TenNCC AS TenNhaCungCap, ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
SUM(ct.SoLuong) AS SoLuongNhap
FROM PHIEU_NHAP_KHO p JOIN CHI_TIET_PHIEU_NHAP ct ON ct.MaPhieuNhap=p.MaPhieuNhap
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu=ct.MaNguyenLieu
LEFT JOIN NHA_CUNG_CAP ncc ON ncc.MaNCC=p.MaNCC
WHERE p.TrangThai <> 'Đã hủy'
GROUP BY p.MaPhieuNhap, p.NgayNhap, p.TrangThai, ncc.TenNCC, ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh;
