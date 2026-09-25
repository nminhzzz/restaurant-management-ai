-- Cashier scope (NFR-12, FR-AI-03): orders, invoices and payments only.
-- No inventory, no purchase prices, no cost columns, no password hashes.
CREATE OR REPLACE VIEW vw_ai_thungan AS
SELECT
    o.MaOrder AS MaOrder,
    o.BusinessDate AS BusinessDate,
    o.LoaiDon AS LoaiDon,
    o.TrangThai AS TrangThaiOrder,
    o.MaBan AS MaBan,
    NULL AS MaHoaDon,
    NULL AS ThoiDiemXuat,
    NULL AS TongTien,
    NULL AS MaGiaoDich,
    NULL AS PhuongThuc,
    NULL AS SoTien
FROM `ORDER` o
UNION ALL
SELECT
    NULL, h.BusinessDate, NULL, NULL, NULL,
    h.MaHoaDon, h.ThoiDiemXuat, h.TongTien, NULL, NULL, NULL
FROM HOA_DON h
UNION ALL
SELECT
    NULL, t.BusinessDate, NULL, NULL, NULL,
    NULL, NULL, NULL, t.MaGiaoDich, t.PhuongThuc, t.SoTien
FROM GIAO_DICH_THANH_TOAN t;
