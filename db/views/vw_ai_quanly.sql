-- TODO(phase-6): replace stub with real per-role column set
-- Manager sees orders + invoices/payments + inventory without GiaVonUocTinh details; MatKhauHash never exposed
CREATE OR REPLACE VIEW vw_ai_quanly AS
SELECT MaOrder, BusinessDate, LoaiDon, TrangThai AS TrangThaiOrder, MaBan FROM `ORDER`;
