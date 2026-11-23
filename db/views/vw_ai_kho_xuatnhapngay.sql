-- One row per business day and ingredient: every movement kind as its own positive
-- quantity (SoLuongDieuChinh keeps its sign), so intake, use and loss by period need no CASE
-- (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_kho_xuatnhapngay AS
SELECT
  g.BusinessDate AS BusinessDate,
  g.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Nhập' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongNhap,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Hủy nhập' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongHuyNhap,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Trừ tự động' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongTieuHao,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Hoàn kho' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongHoanKho,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Xuất thủ công' THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongXuatThuCong,
  SUM(CASE WHEN g.LoaiGiaoDich = 'Điều chỉnh kiểm kê' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongDieuChinh
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu
GROUP BY
  g.BusinessDate,
  g.MaNguyenLieu,
  n.TenNguyenLieu,
  n.DonViTinh;
