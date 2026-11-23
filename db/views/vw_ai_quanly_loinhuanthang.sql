-- One row per business month: revenue, cost of goods and gross profit (FR-REP-04 is a
-- monthly figure). Cost is -GiaTri of the ledger as written at the moving average: draws and
-- returns of finished orders, manual issues and stocktake adjustments; Hủy nhập is not cost
-- and an unvalued movement (GiaTri NULL) is left out, never counted as 0.
CREATE OR REPLACE VIEW vw_ai_quanly_loinhuanthang AS
SELECT
  k.Thang AS Thang,
  SUM(k.DoanhThu) AS DoanhThu,
  SUM(k.GiaVon) AS GiaVon,
  SUM(k.DoanhThu) - SUM(k.GiaVon) AS LoiNhuanGop,
  CASE
    WHEN SUM(k.DoanhThu) = 0 THEN NULL
    ELSE ROUND((SUM(k.DoanhThu) - SUM(k.GiaVon)) * 100 / SUM(k.DoanhThu), 2)
  END AS BienLoiNhuan
FROM (
  SELECT
    DATE_FORMAT(h.BusinessDate, '%Y-%m') AS Thang,
    h.TongTien AS DoanhThu,
    0 AS GiaVon
  FROM HOA_DON AS h
  UNION ALL
  SELECT
    DATE_FORMAT(g.BusinessDate, '%Y-%m') AS Thang,
    0 AS DoanhThu,
    -g.GiaTri AS GiaVon
  FROM GIAO_DICH_KHO AS g
  LEFT JOIN CHI_TIET_ORDER AS ct
    ON ct.MaChiTietOrder = g.MaChiTietOrder
  LEFT JOIN `ORDER` AS o
    ON o.MaOrder = ct.MaOrder
  WHERE
    NOT g.GiaTri IS NULL
    AND (
      (
        g.LoaiGiaoDich IN ('Trừ tự động', 'Hoàn kho')
        AND o.TrangThai IN ('Đã thanh toán', 'Đã hủy', 'Đóng – chưa thu được tiền')
      )
      OR g.LoaiGiaoDich IN ('Xuất thủ công', 'Điều chỉnh kiểm kê')
    )
) AS k
GROUP BY
  k.Thang;
