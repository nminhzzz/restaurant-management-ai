-- TODO(phase-6): replace stub with cashier scope (orders/invoices/payments, no inventory cost)
-- vw_ai_thungan: cashier scope (orders, invoices, payments - no inventory cost)
CREATE OR REPLACE VIEW vw_ai_thungan AS
SELECT MaOrder, BusinessDate, LoaiDon, TrangThai AS TrangThaiOrder, MaBan FROM `ORDER`;
