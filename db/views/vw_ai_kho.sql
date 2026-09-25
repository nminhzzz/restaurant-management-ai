-- Warehouse scope (NFR-12, FR-AI-04): inventory and stock movements.
-- No invoice totals, no revenue, no cost columns, no password hashes.
CREATE OR REPLACE VIEW vw_ai_kho AS
SELECT
    n.MaNguyenLieu AS MaNguyenLieu,
    n.TenNguyenLieu AS TenNguyenLieu,
    n.DonViTinh AS DonViTinh,
    n.SoLuongTon AS SoLuongTon,
    NULL AS MaGiaoDichKho,
    NULL AS BusinessDate,
    NULL AS SoLuong,
    NULL AS LoaiGiaoDich
FROM NGUYEN_LIEU n
UNION ALL
SELECT
    NULL, NULL, NULL, NULL,
    g.MaGiaoDichKho, g.BusinessDate, g.SoLuong, g.LoaiGiaoDich
FROM GIAO_DICH_KHO g;
