SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Cashier / order-staff scope (NFR-12, FR-AI-03): orders, dish-sale lines (selling
-- price only), invoices and payments. No inventory, no purchase prices, no cost or
-- margin columns, no password hashes.
--
-- LoaiBanGhi discriminates the four branches NULL-padded onto a shared column list:
--   'ORDER'      - one row per order
--   'DONG_MON'   - one row per live order line (cancelled lines are excluded)
--   'HOA_DON'    - one row per invoice
--   'THANH_TOAN' - one row per successful payment transaction
CREATE OR REPLACE VIEW vw_ai_thungan AS
SELECT
    CAST('ORDER' AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS LoaiBanGhi,
    o.MaOrder AS MaOrder,
    o.BusinessDate AS BusinessDate,
    o.LoaiDon AS LoaiDon,
    o.TrangThai AS TrangThaiOrder,
    o.MaBan AS MaBan,
    CAST(NULL AS SIGNED) AS MaHoaDon,
    CAST(NULL AS DATETIME) AS ThoiDiemXuat,
    CAST(NULL AS DECIMAL(18, 4)) AS TongTien,
    CAST(NULL AS SIGNED) AS MaGiaoDich,
    CAST(NULL AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS PhuongThuc,
    CAST(NULL AS DECIMAL(18, 4)) AS SoTien,
    CAST(NULL AS CHAR(100)) COLLATE utf8mb4_unicode_ci AS TenMon,
    CAST(NULL AS CHAR(100)) COLLATE utf8mb4_unicode_ci AS TenNhom,
    CAST(NULL AS SIGNED) AS SoLuongMon,
    CAST(NULL AS DECIMAL(18, 4)) AS DonGiaMon,
    CAST(NULL AS DECIMAL(18, 4)) AS ThanhTienMon
FROM `ORDER` o
UNION ALL
SELECT
    'DONG_MON', ct.MaOrder, o.BusinessDate, NULL, o.TrangThai, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    m.TenMon, ng.TenNhomMon, ct.SoLuong, ct.DonGia, ct.ThanhTien
FROM CHI_TIET_ORDER ct
JOIN `ORDER` o ON o.MaOrder = ct.MaOrder
JOIN MON_AN m ON m.MaMon = ct.MaMon
LEFT JOIN NHOM_MON ng ON ng.MaNhomMon = m.MaNhomMon
WHERE ct.TrangThai <> 'Đã hủy'
UNION ALL
SELECT
    'HOA_DON', h.MaOrder, h.BusinessDate, NULL, NULL, NULL,
    h.MaHoaDon, h.ThoiDiemXuat, h.TongTien, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL
FROM HOA_DON h
UNION ALL
SELECT
    'THANH_TOAN', t.MaOrder, t.BusinessDate, NULL, NULL, NULL,
    NULL, NULL, NULL, t.MaGiaoDichTT, t.PhuongThuc, t.SoTien,
    NULL, NULL, NULL, NULL, NULL
FROM GIAO_DICH_THANH_TOAN t
WHERE t.TrangThai = 'Thành công';
