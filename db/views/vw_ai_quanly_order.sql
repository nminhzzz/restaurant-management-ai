-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_order AS
SELECT
  CAST('ORDER' AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS LoaiBanGhi,
  o.MaOrder AS MaOrder,
  o.BusinessDate AS BusinessDate,
  o.LoaiDon AS LoaiDon,
  o.TrangThai AS TrangThaiOrder,
  o.MaBan AS MaBan,
  o.LyDoHuy AS LyDoHuyOrder
FROM `ORDER` AS o;
