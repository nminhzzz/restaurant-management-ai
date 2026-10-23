-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_quanly_suat AS
SELECT m.MaMon, m.TenMon,
CAST(GREATEST(0, MIN(FLOOR(COALESCE(s.SoLuongKhaDung, 0) / ct.DinhLuong))) AS UNSIGNED) AS SoSuatKhaDung,
CURRENT_TIMESTAMP AS ThoiDiemTinh
FROM MON_AN m
JOIN CONG_THUC r ON r.MaCongThuc = (
 SELECT r2.MaCongThuc FROM CONG_THUC r2
 WHERE r2.MaMon=m.MaMon AND r2.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END)
 AND r2.TrangThai IN ('Đang áp dụng', 'Chờ áp dụng')
 ORDER BY r2.BusinessDateApDung DESC, r2.MaCongThuc DESC LIMIT 1
)
JOIN CHI_TIET_CONG_THUC ct ON ct.MaCongThuc=r.MaCongThuc
LEFT JOIN vw_ai_quanly_ton s ON s.MaNguyenLieu=ct.MaNguyenLieu
WHERE m.DaXoa=0 AND m.ChuaCoCongThuc=0 AND m.TamDungThuCong=0 AND ct.DinhLuong>0
GROUP BY m.MaMon, m.TenMon;
