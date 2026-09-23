-- vw_ai_kho: warehouse scope (inventory only)
CREATE OR REPLACE VIEW vw_ai_kho AS
SELECT MaNguyenLieu, TenNguyenLieu, DonViTinh, SoLuongTon FROM NGUYEN_LIEU;
