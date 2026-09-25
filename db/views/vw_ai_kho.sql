-- Warehouse scope (NFR-12, FR-AI-04): current stock, ingredients, minimum-stock
-- warnings, lot/expiry tracking, and stock-movement (receipt/issue) history.
-- No revenue, invoice totals, payments, purchase prices, cost, or password hashes.
--
-- LoaiBanGhi discriminates the three branches NULL-padded onto a shared column list,
-- so the LLM filters by it instead of guessing which columns are populated:
--   'TON_KHO'       - one row per ingredient: current stock + effective min-stock
--   'GIAO_DICH_KHO' - one row per stock movement (receipt/issue/consumption/adjustment)
--   'LO_NGUYEN_LIEU'- one row per ingredient lot, with a computed expiry date
CREATE OR REPLACE VIEW vw_ai_kho AS
SELECT
    CAST('TON_KHO' AS CHAR(20)) AS LoaiBanGhi,
    n.MaNguyenLieu AS MaNguyenLieu,
    n.TenNguyenLieu AS TenNguyenLieu,
    n.DonViTinh AS DonViTinh,
    n.SoLuongTon AS SoLuongTon,
    CASE WHEN n.MucTonToiThieu > 0 THEN n.MucTonToiThieu
         ELSE (SELECT cfg.NguongTonMacDinh FROM CAU_HINH_HE_THONG cfg ORDER BY cfg.MaCauHinh LIMIT 1)
    END AS MucTonToiThieu,
    CASE WHEN n.SoLuongTon < CASE WHEN n.MucTonToiThieu > 0 THEN n.MucTonToiThieu
              ELSE (SELECT cfg.NguongTonMacDinh FROM CAU_HINH_HE_THONG cfg ORDER BY cfg.MaCauHinh LIMIT 1)
         END THEN 1 ELSE 0 END AS CanhBaoTonThap,
    CAST(NULL AS SIGNED) AS MaGiaoDichKho,
    CAST(NULL AS DATE) AS BusinessDate,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuong,
    CAST(NULL AS CHAR(30)) AS LoaiGiaoDich,
    CAST(NULL AS SIGNED) AS MaLo,
    CAST(NULL AS DECIMAL(18, 4)) AS SoLuongConLai,
    CAST(NULL AS CHAR(20)) AS TrangThaiLo,
    CAST(NULL AS DATETIME) AS NgayNhapLo,
    CAST(NULL AS DATE) AS HanSuDungLo
FROM NGUYEN_LIEU n
WHERE n.DaXoa = 0
UNION ALL
SELECT
    'GIAO_DICH_KHO', g.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
    CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS SIGNED),
    g.MaGiaoDichKho, g.BusinessDate, g.SoLuong, g.LoaiGiaoDich,
    CAST(NULL AS SIGNED), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS CHAR(20)),
    CAST(NULL AS DATETIME), CAST(NULL AS DATE)
FROM GIAO_DICH_KHO g
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = g.MaNguyenLieu
UNION ALL
SELECT
    'LO_NGUYEN_LIEU', l.MaNguyenLieu, n.TenNguyenLieu, n.DonViTinh,
    CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS SIGNED),
    CAST(NULL AS SIGNED), CAST(NULL AS DATE), CAST(NULL AS DECIMAL(18, 4)), CAST(NULL AS CHAR(30)),
    l.MaLo, l.SoLuongConLai, l.TrangThai, l.NgayNhap,
    CASE WHEN n.SoNgayBaoQuan IS NULL THEN NULL
         ELSE DATE_ADD(l.NgayNhap, INTERVAL n.SoNgayBaoQuan DAY)
    END
FROM LO_NGUYEN_LIEU l
JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = l.MaNguyenLieu;
