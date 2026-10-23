-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_kho_kiemke AS
SELECT p.MaPhieuKiemKe, CASE WHEN p.NgayKiemKe < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(p.NgayKiemKe)), TIMESTAMP(DATE(p.NgayKiemKe), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(p.NgayKiemKe) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(p.NgayKiemKe), INTERVAL 1 DAY) ELSE DATE(p.NgayKiemKe) END AS BusinessDate,
p.TrangThai, ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
ct.TonHeThong, ct.TonThucTe, ct.ChenhLech
FROM PHIEU_KIEM_KE p JOIN CHI_TIET_KIEM_KE ct ON ct.MaPhieuKiemKe=p.MaPhieuKiemKe
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu=ct.MaNguyenLieu;
