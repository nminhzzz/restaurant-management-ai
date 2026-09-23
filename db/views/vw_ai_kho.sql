-- TODO(phase-6): replace stub with warehouse scope (inventory + movements, no invoice data)
-- vw_ai_kho: warehouse scope (inventory only)
CREATE OR REPLACE VIEW vw_ai_kho AS
SELECT MaNguyenLieu, TenNguyenLieu, DonViTinh, SoLuongTon FROM NGUYEN_LIEU;
