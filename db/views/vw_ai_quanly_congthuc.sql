-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_quanly_congthuc AS
SELECT r.MaCongThuc, r.MaMon, m.TenMon, r.BusinessDateApDung, r.TrangThai,
ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh, ct.DinhLuong
FROM CONG_THUC r JOIN MON_AN m ON m.MaMon=r.MaMon
JOIN CHI_TIET_CONG_THUC ct ON ct.MaCongThuc=r.MaCongThuc
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu=ct.MaNguyenLieu;
