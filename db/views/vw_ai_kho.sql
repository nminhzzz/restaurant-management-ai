-- Warehouse scope (NFR-12, FR-AI-04): current stock, ingredients, minimum-stock
-- warnings, lot/expiry tracking, and stock-movement (receipt/issue) history.
-- No revenue, invoice totals, payments, purchase prices, cost, or password hashes.
--
-- LoaiBanGhi discriminates the three branches NULL-padded onto a shared column list,
-- so the LLM filters by it instead of guessing which columns are populated:
--   'TON_KHO'       - one row per ingredient: stock + held/available eligible-lot quantities
--   'GIAO_DICH_KHO' - one row per stock movement (receipt/issue/consumption/adjustment)
--   'LO_NGUYEN_LIEU'- one row per ingredient lot, with a computed expiry date
CREATE OR REPLACE VIEW vw_ai_kho AS
SELECT
    CAST('TON_KHO' AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS LoaiBanGhi,
    n.MaNguyenLieu AS MaNguyenLieu,
    n.TenNguyenLieu AS TenNguyenLieu,
    n.DonViTinh AS DonViTinh,
    n.SoLuongTon AS SoLuongTon,
    CAST(COALESCE(ton_kho.SoLuongGiu, 0) AS DECIMAL(18, 4)) AS SoLuongGiu,
    CAST(COALESCE(ton_kho.SoLuongKhaDung, 0) AS DECIMAL(18, 4)) AS SoLuongKhaDung,
    COALESCE(n.MucTonToiThieu, (SELECT cfg.NguongTonMacDinh FROM CAU_HINH_HE_THONG cfg ORDER BY cfg.MaCauHinh LIMIT 1)) AS MucTonToiThieu,
    CASE WHEN n.SoLuongTon < COALESCE(n.MucTonToiThieu, (SELECT cfg.NguongTonMacDinh FROM CAU_HINH_HE_THONG cfg ORDER BY cfg.MaCauHinh LIMIT 1)) THEN 1 ELSE 0 END AS CanhBaoTonThap,
    CAST(NULL AS SIGNED) AS MaGiaoDichKho,
    CAST(NULL AS DATE) AS BusinessDate,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuong,
    CAST(NULL AS CHAR(30)) COLLATE utf8mb4_unicode_ci AS LoaiGiaoDich,
    CAST(NULL AS SIGNED) AS MaLo,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuongConLai,
    CAST(NULL AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS TrangThaiLo,
    CAST(NULL AS DATETIME) AS NgayNhapLo,
    CAST(NULL AS DATE) AS HanSuDungLo
FROM NGUYEN_LIEU n
LEFT JOIN (
    SELECT
        l.MaNguyenLieu,
        SUM(COALESCE(giu.SoLuongGiu, 0)) AS SoLuongGiu,
        SUM(GREATEST(l.SoLuongConLai - COALESCE(giu.SoLuongGiu, 0), 0)) AS SoLuongKhaDung
    FROM LO_NGUYEN_LIEU l
    LEFT JOIN (
        SELECT
            ct.MaLoNguyenLieu,
            SUM(ct.SoLuongGiu) AS SoLuongGiu
        FROM CHI_TIET_GIU_CHO ct
        JOIN GIU_CHO_MON gh ON gh.MaGiuCho = ct.MaGiuCho
        WHERE gh.TrangThai = 'Đang giữ'
          AND gh.ThoiDiemHetHan > CURRENT_TIMESTAMP
        GROUP BY ct.MaLoNguyenLieu
    ) giu ON giu.MaLoNguyenLieu = l.MaLoNguyenLieu
    WHERE l.SoLuongConLai > 0
      AND l.TrangThai <> 'Hết hạn'
      AND (l.HanSuDung IS NULL OR DATE_ADD(l.HanSuDung, INTERVAL 1 DAY) > CURRENT_TIMESTAMP)
    GROUP BY l.MaNguyenLieu
) ton_kho ON ton_kho.MaNguyenLieu = n.MaNguyenLieu
WHERE n.DaXoa = 0
UNION ALL
SELECT
    'GIAO_DICH_KHO', g.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
    CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS DECIMAL(18, 4)),
    CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS SIGNED),
    g.MaGiaoDichKho, g.BusinessDate, g.SoLuongThayDoi, g.LoaiGiaoDich,
    CAST(NULL AS SIGNED), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS CHAR(20)) COLLATE utf8mb4_unicode_ci,
    CAST(NULL AS DATETIME), CAST(NULL AS DATE)
FROM GIAO_DICH_KHO g
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = g.MaNguyenLieu
UNION ALL
SELECT
    'LO_NGUYEN_LIEU', l.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
    CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS DECIMAL(18, 4)),
    CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS SIGNED),
    CAST(NULL AS SIGNED), CAST(NULL AS DATE), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS CHAR(30)) COLLATE utf8mb4_unicode_ci,
    l.MaLoNguyenLieu, l.SoLuongConLai, l.TrangThai, l.NgayNhap,
    l.HanSuDung
FROM LO_NGUYEN_LIEU l
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = l.MaNguyenLieu;
