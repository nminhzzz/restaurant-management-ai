-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_quanly_xuat AS
SELECT p.MaPhieuXuat, CASE WHEN p.NgayXuat < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(p.NgayXuat)), TIMESTAMP(DATE(p.NgayXuat), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(p.NgayXuat) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(p.NgayXuat), INTERVAL 1 DAY) ELSE DATE(p.NgayXuat) END AS BusinessDate,
p.TrangThai, p.LyDo, ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
SUM(ct.SoLuong) AS SoLuong
FROM PHIEU_XUAT_KHO p JOIN CHI_TIET_PHIEU_XUAT ct ON ct.MaPhieuXuat=p.MaPhieuXuat
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu=ct.MaNguyenLieu
GROUP BY p.MaPhieuXuat, p.NgayXuat, p.TrangThai, p.LyDo, ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh;
