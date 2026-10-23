-- One row per topic record; no joins to other one-to-many topics.
CREATE OR REPLACE VIEW vw_ai_quanly_ton AS
SELECT
  'TON_KHO' AS LoaiBanGhi,
  n.MaNguyenLieu AS MaNguyenLieu,
  n.TenNguyenLieu AS TenNguyenLieu,
  n.DonViTinh AS DonViTinh,
  n.SoLuongTon AS SoLuongTon,
  CURRENT_TIMESTAMP AS ThoiDiemTinh,
  (SELECT COALESCE(SUM(l.SoLuongConLai), 0) FROM LO_NGUYEN_LIEU l
   WHERE l.MaNguyenLieu=n.MaNguyenLieu AND l.SoLuongConLai>0 AND l.TrangThai<>'Hết hạn'
   AND (l.HanSuDung IS NULL OR DATE_ADD(l.HanSuDung, INTERVAL 1 DAY)>CURRENT_TIMESTAMP)) AS SoLuongDuDieuKien,
  CASE
    WHEN n.MucTonToiThieu > 0
    THEN n.MucTonToiThieu
    ELSE (
      SELECT
        cfg.NguongTonMacDinh
      FROM CAU_HINH_HE_THONG AS cfg
      ORDER BY
        cfg.MaCauHinh
      LIMIT 1
    )
  END AS MucTonToiThieu,
  CAST((
    SELECT
      COALESCE(SUM(d.SoLuongGiu), 0)
    FROM CHI_TIET_GIU_CHO AS d
    JOIN GIU_CHO_MON AS g
      ON g.MaGiuCho = d.MaGiuCho
    JOIN LO_NGUYEN_LIEU AS l
      ON l.MaLoNguyenLieu = d.MaLoNguyenLieu
    WHERE
      l.MaNguyenLieu = n.MaNguyenLieu
      AND g.TrangThai = 'Đang giữ'
      AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()
      AND l.SoLuongConLai > 0
      AND l.TrangThai <> 'Hết hạn'
      AND (
        l.HanSuDung IS NULL
        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()
      )
  ) AS DECIMAL(18, 4)) AS SoLuongGiu,
  CAST((
    SELECT
      COALESCE(
        SUM(
          GREATEST(
            0,
            l.SoLuongConLai - (
              SELECT
                COALESCE(SUM(d.SoLuongGiu), 0)
              FROM CHI_TIET_GIU_CHO AS d
              JOIN GIU_CHO_MON AS g
                ON g.MaGiuCho = d.MaGiuCho
              WHERE
                d.MaLoNguyenLieu = l.MaLoNguyenLieu
                AND g.TrangThai = 'Đang giữ'
                AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()
            )
          )
        ),
        0
      )
    FROM LO_NGUYEN_LIEU AS l
    WHERE
      l.MaNguyenLieu = n.MaNguyenLieu
      AND l.SoLuongConLai > 0
      AND l.TrangThai <> 'Hết hạn'
      AND (
        l.HanSuDung IS NULL
        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()
      )
  ) AS DECIMAL(18, 4)) AS SoLuongKhaDung
FROM NGUYEN_LIEU AS n
WHERE
  n.DaXoa = 0;
