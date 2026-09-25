-- Manager scope (NFR-12, FR-AI-02): the full scope of Cashier + Warehouse, plus
-- cancel reasons, dish-level sales, monthly average ingredient cost and receipt
-- purchase prices needed for gross margin, cost, and cancelled-order reporting.
-- Never a password hash.
--
-- LoaiBanGhi discriminates the eight branches NULL-padded onto a shared column list,
-- so an aggregate such as SUM(TongTien) or SUM(SoTien) simply ignores rows that do
-- not carry it, and the LLM filters branches by LoaiBanGhi instead of guessing:
--   'ORDER'         - one row per order (incl. cancel reason)
--   'DONG_MON'      - one row per order line (dish, quantity, selling price)
--   'HOA_DON'       - one row per invoice
--   'THANH_TOAN'    - one row per payment transaction
--   'TON_KHO'       - one row per ingredient: current stock + effective min-stock
--   'GIA_VON_THANG' - one row per ingredient per month: weighted-average purchase cost
--   'GIAO_DICH_KHO' - one row per stock movement (receipt/issue/consumption/adjustment)
--   'PHIEU_NHAP'    - one row per goods-receipt line: supplier + purchase price
CREATE OR REPLACE VIEW vw_ai_quanly AS
SELECT
    CAST('ORDER' AS CHAR(20)) AS LoaiBanGhi,
    o.MaOrder AS MaOrder,
    o.BusinessDate AS BusinessDate,
    o.LoaiDon AS LoaiDon,
    o.TrangThai AS TrangThaiOrder,
    o.MaBan AS MaBan,
    o.LyDoHuy AS LyDoHuyOrder,
    CAST(NULL AS SIGNED) AS MaHoaDon,
    CAST(NULL AS DATETIME) AS ThoiDiemXuat,
    CAST(NULL AS DECIMAL(18, 4)) AS TongTien,
    CAST(NULL AS SIGNED) AS MaGiaoDich,
    CAST(NULL AS CHAR(20)) AS PhuongThuc,
    CAST(NULL AS DECIMAL(18, 4)) AS SoTien,
    CAST(NULL AS CHAR(100)) AS TenMon,
    CAST(NULL AS CHAR(100)) AS TenNhom,
    CAST(NULL AS SIGNED) AS SoLuongMon,
    CAST(NULL AS DECIMAL(18, 4)) AS DonGiaMon,
    CAST(NULL AS DECIMAL(18, 4)) AS ThanhTienMon,
    CAST(NULL AS SIGNED) AS MaNguyenLieu,
    CAST(NULL AS CHAR(100)) AS TenNguyenLieu,
    CAST(NULL AS CHAR(20)) AS DonViTinh,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuongTon,
    CAST(NULL AS DECIMAL(18, 4)) AS MucTonToiThieu,
    CAST(NULL AS SIGNED) AS Thang,
    CAST(NULL AS DECIMAL(18, 4)) AS GiaBinhQuanThang,
    CAST(NULL AS DECIMAL(18, 4)) AS TongSoLuongNhapThang,
    CAST(NULL AS SIGNED) AS MaGiaoDichKho,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuong,
    CAST(NULL AS CHAR(30)) AS LoaiGiaoDich,
    CAST(NULL AS SIGNED) AS MaPhieuNhap,
    CAST(NULL AS CHAR(100)) AS TenNhaCungCap,
    CAST(NULL AS DECIMAL(18, 4)) AS DonGiaNhap,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuongNhap
FROM `ORDER` o
UNION ALL
SELECT
    'DONG_MON', ct.MaOrder, o.BusinessDate, NULL, o.TrangThai, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    m.TenMon, ng.TenNhom, ct.SoLuong, ct.DonGia, ct.SoLuong * ct.DonGia,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL
FROM CHI_TIET_ORDER ct
JOIN `ORDER` o ON o.MaOrder = ct.MaOrder
JOIN MON_AN m ON m.MaMon = ct.MaMon
LEFT JOIN NHOM_MON ng ON ng.MaNhomMon = m.MaNhomMon
UNION ALL
SELECT
    'HOA_DON', h.MaOrder, h.BusinessDate, NULL, NULL, NULL, NULL,
    h.MaHoaDon, h.ThoiDiemXuat, h.TongTien, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL
FROM HOA_DON h
UNION ALL
SELECT
    'THANH_TOAN', t.MaOrder, t.BusinessDate, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, t.MaGiaoDich, t.PhuongThuc, t.SoTien,
    NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL
FROM GIAO_DICH_THANH_TOAN t
UNION ALL
SELECT
    'TON_KHO', NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL,
    n.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh, n.SoLuongTon,
    CASE WHEN n.MucTonToiThieu > 0 THEN n.MucTonToiThieu
         ELSE (SELECT cfg.NguongTonMacDinh FROM CAU_HINH_HE_THONG cfg ORDER BY cfg.MaCauHinh LIMIT 1)
    END,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM NGUYEN_LIEU n
WHERE n.DaXoa = 0
UNION ALL
SELECT
    'GIA_VON_THANG', NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL,
    gv.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh, NULL, NULL,
    gv.Thang, gv.GiaBinhQuan, gv.TongSoLuongNhap,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM GIA_BINH_QUAN_THANG gv
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = gv.MaNguyenLieu
UNION ALL
SELECT
    'GIAO_DICH_KHO', NULL, g.BusinessDate, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL,
    g.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh, NULL, NULL,
    NULL, NULL, NULL,
    g.MaGiaoDichKho, g.SoLuong, g.LoaiGiaoDich, NULL, NULL, NULL, NULL
FROM GIAO_DICH_KHO g
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = g.MaNguyenLieu
UNION ALL
SELECT
    'PHIEU_NHAP', NULL, DATE(pn.NgayNhap), NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL,
    ct.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh, NULL, NULL,
    NULL, NULL, NULL,
    NULL, NULL, NULL,
    pn.MaPhieuNhap, ncc.TenNhaCungCap, ct.DonGia, ct.SoLuong
FROM CHI_TIET_PHIEU_NHAP ct
JOIN PHIEU_NHAP_KHO pn ON pn.MaPhieuNhap = ct.MaPhieuNhap
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = ct.MaNguyenLieu
LEFT JOIN NHA_CUNG_CAP ncc ON ncc.MaNhaCungCap = pn.MaNhaCungCap;
