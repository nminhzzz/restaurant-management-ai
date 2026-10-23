-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_quanly_nguyenlieu AS
SELECT MaNguyenLieu, TenNguyenLieu, DonViTinh, SoNgayBaoQuan, MucTonToiThieu FROM NGUYEN_LIEU WHERE DaXoa=0;
