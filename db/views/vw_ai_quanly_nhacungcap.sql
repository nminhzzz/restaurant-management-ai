-- Topic view; only the explicit projected columns are exposed.
CREATE OR REPLACE VIEW vw_ai_quanly_nhacungcap AS
SELECT MaNCC, TenNCC FROM NHA_CUNG_CAP WHERE DaXoa=0;
