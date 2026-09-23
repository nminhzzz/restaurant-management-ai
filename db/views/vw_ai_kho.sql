-- TODO(phase-6): replace stub with warehouse scope
-- Warehouse: inventory + movements, no invoice totals and no user hashes
CREATE OR REPLACE VIEW vw_ai_kho AS
SELECT MaNguyenLieu, TenNguyenLieu, DonViTinh, SoLuongTon FROM NGUYEN_LIEU;
