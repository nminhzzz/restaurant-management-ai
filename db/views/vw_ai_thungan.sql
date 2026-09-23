-- TODO(phase-6): replace stub with cashier scope
-- Cashier: orders/invoices/payments only, no inventory cost columns (GiaVonUocTinh) and no user hashes
CREATE OR REPLACE VIEW vw_ai_thungan AS
SELECT MaOrder, BusinessDate, LoaiDon, TrangThai AS TrangThaiOrder, MaBan FROM `ORDER`;
