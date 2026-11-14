-- One row per business day and ingredient: every movement kind as its own positive
-- quantity (SoLuongDieuChinh keeps its sign), so intake, use and loss by period need no CASE
-- (precomputed metric group, v2).
CREATE OR REPLACE VIEW vw_ai_quanly_xuatnhapngay AS
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
  SUM(CASE WHEN g.LoaiGiaoDich = 'Điều chỉnh kiểm kê' THEN g.SoLuongThayDoi ELSE 0 END) AS SoLuongDieuChinh,
  SUM(CASE WHEN NOT g.GiaTri IS NULL
    AND (
      (
        g.LoaiGiaoDich IN ('Trừ tự động', 'Hoàn kho')
        AND o.TrangThai IN ('Đã thanh toán', 'Đã hủy', 'Đóng – chưa thu được tiền')
      )
      OR g.LoaiGiaoDich IN ('Xuất thủ công', 'Điều chỉnh kiểm kê')
    ) THEN -g.GiaTri ELSE 0 END) AS GiaVon,
  SUM(CASE WHEN NOT g.GiaTri IS NULL
    AND (
      (
        g.LoaiGiaoDich IN ('Trừ tự động', 'Hoàn kho')
        AND o.TrangThai IN ('Đã thanh toán', 'Đã hủy', 'Đóng – chưa thu được tiền')
      )
      OR g.LoaiGiaoDich IN ('Xuất thủ công', 'Điều chỉnh kiểm kê')
    ) THEN -g.SoLuongThayDoi ELSE 0 END) AS SoLuongGiaVon
FROM GIAO_DICH_KHO AS g
JOIN NGUYEN_LIEU AS n
  ON n.MaNguyenLieu = g.MaNguyenLieu
LEFT JOIN CHI_TIET_ORDER AS ct
  ON ct.MaChiTietOrder = g.MaChiTietOrder
LEFT JOIN `ORDER` AS o
  ON o.MaOrder = ct.MaOrder
GROUP BY
  g.BusinessDate,
  g.MaNguyenLieu,
  n.TenNguyenLieu,
  n.DonViTinh;
