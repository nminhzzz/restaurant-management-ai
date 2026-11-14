-- One row per invoice with the order's table, order type and issue hour, so revenue by
-- table, order type, hour, day or month needs no join (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_thungan_doanhthu AS
SELECT
  h.MaHoaDon AS MaHoaDon,
  h.MaOrder AS MaOrder,
  h.BusinessDate AS BusinessDate,
  DATE_FORMAT(h.BusinessDate, '%Y-%m') AS Thang,
  HOUR(h.ThoiDiemXuat) AS Gio,
  o.MaBan AS MaBan,
  o.LoaiDon AS LoaiDon,
  h.TongTien AS DoanhThu
FROM HOA_DON AS h
JOIN `ORDER` AS o
  ON o.MaOrder = h.MaOrder;
