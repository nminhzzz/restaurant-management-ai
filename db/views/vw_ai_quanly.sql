-- Manager scope (NFR-12): orders, invoices, payments and inventory — without cost
-- details, and never a password hash.
--
-- One view answers every question this role may ask, so the assistant is only ever
-- told about a single relation. The branches are NULL-padded onto a shared column
-- list: an aggregate like SUM(TongTien) simply ignores the rows that do not carry it.
CREATE OR REPLACE VIEW vw_ai_quanly AS
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
    NULL AS SoTien,
    NULL AS MaNguyenLieu,
    NULL AS TenNguyenLieu,
    NULL AS DonViTinh,
    NULL AS SoLuongTon
FROM `ORDER` o
UNION ALL
SELECT
    NULL, h.BusinessDate, NULL, NULL, NULL,
    h.MaHoaDon, h.ThoiDiemXuat, h.TongTien, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL
FROM HOA_DON h
UNION ALL
SELECT
    NULL, t.BusinessDate, NULL, NULL, NULL,
    NULL, NULL, NULL, t.MaGiaoDich, t.PhuongThuc, t.SoTien,
    NULL, NULL, NULL, NULL
FROM GIAO_DICH_THANH_TOAN t
UNION ALL
SELECT
    NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    n.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh, n.SoLuongTon
FROM NGUYEN_LIEU n;
