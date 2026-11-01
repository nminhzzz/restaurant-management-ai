-- Topic view; only the explicit projected columns are exposed.
-- TrangThai is derived (FR-CAT-27): MON_AN stores neither HetNguyenLieu nor TrangThai.
CREATE OR REPLACE VIEW vw_ai_thungan_mon AS
SELECT m.MaMon, m.TenMon, n.TenNhomMon AS TenNhom,
CASE
 WHEN m.ChuaCoCongThuc=1 THEN 'Nháp'
 WHEN EXISTS (
  SELECT 1 FROM CHI_TIET_CONG_THUC ct
  WHERE ct.MaCongThuc = (
   SELECT r2.MaCongThuc FROM CONG_THUC r2
   WHERE r2.MaMon=m.MaMon AND r2.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END)
   AND r2.TrangThai IN ('Đang áp dụng', 'Chờ áp dụng')
   ORDER BY r2.BusinessDateApDung DESC, r2.MaCongThuc DESC LIMIT 1
  )
  AND ct.DinhLuong>0
  AND COALESCE((SELECT s.SoLuongKhaDung FROM vw_ai_quanly_ton s WHERE s.MaNguyenLieu=ct.MaNguyenLieu), 0) < ct.DinhLuong
 ) THEN 'Hết nguyên liệu'
 WHEN m.TamDungThuCong=1 THEN 'Tạm dừng phục vụ'
 ELSE 'Hoạt động'
END AS TrangThai,
(SELECT g.GiaBan FROM LICH_SU_GIA_MON g WHERE g.MaMon=m.MaMon
 AND g.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END) AND g.TrangThai IN ('Đang áp dụng','Chờ áp dụng')
 ORDER BY g.BusinessDateApDung DESC,g.MaPhienBanGia DESC LIMIT 1) AS GiaBan
FROM MON_AN m LEFT JOIN NHOM_MON n ON n.MaNhomMon=m.MaNhomMon WHERE m.DaXoa=0;
