"""Per-ingredient stock threshold: NULL means "use the system default", 0 is a real threshold.

FR-INV (stock alerts): before this revision 0 doubled as "use the default", so an ingredient
could never have an own threshold of 0. Existing 0 rows are turned into NULL to keep behaving
as they did. The two stock views are redefined to test IS NOT NULL instead of > 0.
"""

import sqlalchemy as sa
from alembic import op

revision = "d01112600001"
down_revision = "d23102300006"
branch_labels = None
depends_on = None

# op.f() keeps the exact name the initial schema gave the constraint.
CK_MIN_STOCK = op.f("ck_NGUYEN_LIEU_min_stock_non_negative")

NEW_VIEWS = {
    "vw_ai_kho_ton": "-- One row per topic record; no joins to other one-to-many topics.\nCREATE OR REPLACE VIEW vw_ai_kho_ton AS\nSELECT\n  CAST('TON_KHO' AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS LoaiBanGhi,\n  n.MaNguyenLieu AS MaNguyenLieu,\n  n.TenNguyenLieu AS TenNguyenLieu,\n  n.DonViTinh AS DonViTinh,\n  n.SoLuongTon AS SoLuongTon,\n  CURRENT_TIMESTAMP AS ThoiDiemTinh,\n  (SELECT COALESCE(SUM(l.SoLuongConLai), 0) FROM LO_NGUYEN_LIEU l\n   WHERE l.MaNguyenLieu=n.MaNguyenLieu AND l.SoLuongConLai>0 AND l.TrangThai<>'Hết hạn'\n   AND (l.HanSuDung IS NULL OR DATE_ADD(l.HanSuDung, INTERVAL 1 DAY)>CURRENT_TIMESTAMP)) AS SoLuongDuDieuKien,\n  CAST((\n    SELECT\n      COALESCE(SUM(d.SoLuongGiu), 0)\n    FROM CHI_TIET_GIU_CHO AS d\n    JOIN GIU_CHO_MON AS g\n      ON g.MaGiuCho = d.MaGiuCho\n    JOIN LO_NGUYEN_LIEU AS l\n      ON l.MaLoNguyenLieu = d.MaLoNguyenLieu\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND g.TrangThai = 'Đang giữ'\n      AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongGiu,\n  CAST((\n    SELECT\n      COALESCE(\n        SUM(\n          GREATEST(\n            0,\n            l.SoLuongConLai - (\n              SELECT\n                COALESCE(SUM(d.SoLuongGiu), 0)\n              FROM CHI_TIET_GIU_CHO AS d\n              JOIN GIU_CHO_MON AS g\n                ON g.MaGiuCho = d.MaGiuCho\n              WHERE\n                d.MaLoNguyenLieu = l.MaLoNguyenLieu\n                AND g.TrangThai = 'Đang giữ'\n                AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n            )\n          )\n        ),\n        0\n      )\n    FROM LO_NGUYEN_LIEU AS l\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongKhaDung,\n  CASE\n    WHEN n.MucTonToiThieu IS NOT NULL\n    THEN n.MucTonToiThieu\n    ELSE (\n      SELECT\n        cfg.NguongTonMacDinh\n      FROM CAU_HINH_HE_THONG AS cfg\n      ORDER BY\n        cfg.MaCauHinh\n      LIMIT 1\n    )\n  END AS MucTonToiThieu,\n  CASE\n    WHEN n.SoLuongTon < CASE\n      WHEN n.MucTonToiThieu IS NOT NULL\n      THEN n.MucTonToiThieu\n      ELSE (\n        SELECT\n          cfg.NguongTonMacDinh\n        FROM CAU_HINH_HE_THONG AS cfg\n        ORDER BY\n          cfg.MaCauHinh\n        LIMIT 1\n      )\n    END\n    THEN 1\n    ELSE 0\n  END AS CanhBaoTonThap\nFROM NGUYEN_LIEU AS n\nWHERE\n  n.DaXoa = 0;",
    "vw_ai_quanly_ton": "-- One row per topic record; no joins to other one-to-many topics.\nCREATE OR REPLACE VIEW vw_ai_quanly_ton AS\nSELECT\n  'TON_KHO' AS LoaiBanGhi,\n  n.MaNguyenLieu AS MaNguyenLieu,\n  n.TenNguyenLieu AS TenNguyenLieu,\n  n.DonViTinh AS DonViTinh,\n  n.SoLuongTon AS SoLuongTon,\n  CURRENT_TIMESTAMP AS ThoiDiemTinh,\n  (SELECT COALESCE(SUM(l.SoLuongConLai), 0) FROM LO_NGUYEN_LIEU l\n   WHERE l.MaNguyenLieu=n.MaNguyenLieu AND l.SoLuongConLai>0 AND l.TrangThai<>'Hết hạn'\n   AND (l.HanSuDung IS NULL OR DATE_ADD(l.HanSuDung, INTERVAL 1 DAY)>CURRENT_TIMESTAMP)) AS SoLuongDuDieuKien,\n  CASE\n    WHEN n.MucTonToiThieu IS NOT NULL\n    THEN n.MucTonToiThieu\n    ELSE (\n      SELECT\n        cfg.NguongTonMacDinh\n      FROM CAU_HINH_HE_THONG AS cfg\n      ORDER BY\n        cfg.MaCauHinh\n      LIMIT 1\n    )\n  END AS MucTonToiThieu,\n  CAST((\n    SELECT\n      COALESCE(SUM(d.SoLuongGiu), 0)\n    FROM CHI_TIET_GIU_CHO AS d\n    JOIN GIU_CHO_MON AS g\n      ON g.MaGiuCho = d.MaGiuCho\n    JOIN LO_NGUYEN_LIEU AS l\n      ON l.MaLoNguyenLieu = d.MaLoNguyenLieu\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND g.TrangThai = 'Đang giữ'\n      AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongGiu,\n  CAST((\n    SELECT\n      COALESCE(\n        SUM(\n          GREATEST(\n            0,\n            l.SoLuongConLai - (\n              SELECT\n                COALESCE(SUM(d.SoLuongGiu), 0)\n              FROM CHI_TIET_GIU_CHO AS d\n              JOIN GIU_CHO_MON AS g\n                ON g.MaGiuCho = d.MaGiuCho\n              WHERE\n                d.MaLoNguyenLieu = l.MaLoNguyenLieu\n                AND g.TrangThai = 'Đang giữ'\n                AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n            )\n          )\n        ),\n        0\n      )\n    FROM LO_NGUYEN_LIEU AS l\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongKhaDung\nFROM NGUYEN_LIEU AS n\nWHERE\n  n.DaXoa = 0;",
}

OLD_VIEWS = {
    "vw_ai_kho_ton": "-- One row per topic record; no joins to other one-to-many topics.\nCREATE OR REPLACE VIEW vw_ai_kho_ton AS\nSELECT\n  CAST('TON_KHO' AS CHAR(20)) COLLATE utf8mb4_unicode_ci AS LoaiBanGhi,\n  n.MaNguyenLieu AS MaNguyenLieu,\n  n.TenNguyenLieu AS TenNguyenLieu,\n  n.DonViTinh AS DonViTinh,\n  n.SoLuongTon AS SoLuongTon,\n  CURRENT_TIMESTAMP AS ThoiDiemTinh,\n  (SELECT COALESCE(SUM(l.SoLuongConLai), 0) FROM LO_NGUYEN_LIEU l\n   WHERE l.MaNguyenLieu=n.MaNguyenLieu AND l.SoLuongConLai>0 AND l.TrangThai<>'Hết hạn'\n   AND (l.HanSuDung IS NULL OR DATE_ADD(l.HanSuDung, INTERVAL 1 DAY)>CURRENT_TIMESTAMP)) AS SoLuongDuDieuKien,\n  CAST((\n    SELECT\n      COALESCE(SUM(d.SoLuongGiu), 0)\n    FROM CHI_TIET_GIU_CHO AS d\n    JOIN GIU_CHO_MON AS g\n      ON g.MaGiuCho = d.MaGiuCho\n    JOIN LO_NGUYEN_LIEU AS l\n      ON l.MaLoNguyenLieu = d.MaLoNguyenLieu\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND g.TrangThai = 'Đang giữ'\n      AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongGiu,\n  CAST((\n    SELECT\n      COALESCE(\n        SUM(\n          GREATEST(\n            0,\n            l.SoLuongConLai - (\n              SELECT\n                COALESCE(SUM(d.SoLuongGiu), 0)\n              FROM CHI_TIET_GIU_CHO AS d\n              JOIN GIU_CHO_MON AS g\n                ON g.MaGiuCho = d.MaGiuCho\n              WHERE\n                d.MaLoNguyenLieu = l.MaLoNguyenLieu\n                AND g.TrangThai = 'Đang giữ'\n                AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n            )\n          )\n        ),\n        0\n      )\n    FROM LO_NGUYEN_LIEU AS l\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongKhaDung,\n  CASE\n    WHEN n.MucTonToiThieu > 0\n    THEN n.MucTonToiThieu\n    ELSE (\n      SELECT\n        cfg.NguongTonMacDinh\n      FROM CAU_HINH_HE_THONG AS cfg\n      ORDER BY\n        cfg.MaCauHinh\n      LIMIT 1\n    )\n  END AS MucTonToiThieu,\n  CASE\n    WHEN n.SoLuongTon < CASE\n      WHEN n.MucTonToiThieu > 0\n      THEN n.MucTonToiThieu\n      ELSE (\n        SELECT\n          cfg.NguongTonMacDinh\n        FROM CAU_HINH_HE_THONG AS cfg\n        ORDER BY\n          cfg.MaCauHinh\n        LIMIT 1\n      )\n    END\n    THEN 1\n    ELSE 0\n  END AS CanhBaoTonThap\nFROM NGUYEN_LIEU AS n\nWHERE\n  n.DaXoa = 0;",
    "vw_ai_quanly_ton": "-- One row per topic record; no joins to other one-to-many topics.\nCREATE OR REPLACE VIEW vw_ai_quanly_ton AS\nSELECT\n  'TON_KHO' AS LoaiBanGhi,\n  n.MaNguyenLieu AS MaNguyenLieu,\n  n.TenNguyenLieu AS TenNguyenLieu,\n  n.DonViTinh AS DonViTinh,\n  n.SoLuongTon AS SoLuongTon,\n  CURRENT_TIMESTAMP AS ThoiDiemTinh,\n  (SELECT COALESCE(SUM(l.SoLuongConLai), 0) FROM LO_NGUYEN_LIEU l\n   WHERE l.MaNguyenLieu=n.MaNguyenLieu AND l.SoLuongConLai>0 AND l.TrangThai<>'Hết hạn'\n   AND (l.HanSuDung IS NULL OR DATE_ADD(l.HanSuDung, INTERVAL 1 DAY)>CURRENT_TIMESTAMP)) AS SoLuongDuDieuKien,\n  CASE\n    WHEN n.MucTonToiThieu > 0\n    THEN n.MucTonToiThieu\n    ELSE (\n      SELECT\n        cfg.NguongTonMacDinh\n      FROM CAU_HINH_HE_THONG AS cfg\n      ORDER BY\n        cfg.MaCauHinh\n      LIMIT 1\n    )\n  END AS MucTonToiThieu,\n  CAST((\n    SELECT\n      COALESCE(SUM(d.SoLuongGiu), 0)\n    FROM CHI_TIET_GIU_CHO AS d\n    JOIN GIU_CHO_MON AS g\n      ON g.MaGiuCho = d.MaGiuCho\n    JOIN LO_NGUYEN_LIEU AS l\n      ON l.MaLoNguyenLieu = d.MaLoNguyenLieu\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND g.TrangThai = 'Đang giữ'\n      AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongGiu,\n  CAST((\n    SELECT\n      COALESCE(\n        SUM(\n          GREATEST(\n            0,\n            l.SoLuongConLai - (\n              SELECT\n                COALESCE(SUM(d.SoLuongGiu), 0)\n              FROM CHI_TIET_GIU_CHO AS d\n              JOIN GIU_CHO_MON AS g\n                ON g.MaGiuCho = d.MaGiuCho\n              WHERE\n                d.MaLoNguyenLieu = l.MaLoNguyenLieu\n                AND g.TrangThai = 'Đang giữ'\n                AND g.ThoiDiemHetHan > CURRENT_TIMESTAMP()\n            )\n          )\n        ),\n        0\n      )\n    FROM LO_NGUYEN_LIEU AS l\n    WHERE\n      l.MaNguyenLieu = n.MaNguyenLieu\n      AND l.SoLuongConLai > 0\n      AND l.TrangThai <> 'Hết hạn'\n      AND (\n        l.HanSuDung IS NULL\n        OR DATE_ADD(l.HanSuDung, INTERVAL '1' DAY) > CURRENT_TIMESTAMP()\n      )\n  ) AS DECIMAL(18, 4)) AS SoLuongKhaDung\nFROM NGUYEN_LIEU AS n\nWHERE\n  n.DaXoa = 0;",
}


def _replace_views(views: dict[str, str]) -> None:
    # vw_ai_kho_suat / vw_ai_quanly_suat select from the *_ton views, so only the
    # base views are replaced; MySQL keeps dependents valid while column names are unchanged.
    for ddl in views.values():
        op.execute(ddl)


def upgrade() -> None:
    op.drop_constraint(CK_MIN_STOCK, "NGUYEN_LIEU", type_="check")
    op.alter_column(
        "NGUYEN_LIEU",
        "MucTonToiThieu",
        existing_type=sa.DECIMAL(precision=18, scale=4),
        nullable=True,
    )
    op.execute("UPDATE NGUYEN_LIEU SET MucTonToiThieu = NULL WHERE MucTonToiThieu = 0")
    op.create_check_constraint(
        CK_MIN_STOCK,
        "NGUYEN_LIEU",
        "MucTonToiThieu IS NULL OR MucTonToiThieu >= 0",
    )
    _replace_views(NEW_VIEWS)


def downgrade() -> None:
    _replace_views(OLD_VIEWS)
    op.drop_constraint(CK_MIN_STOCK, "NGUYEN_LIEU", type_="check")
    op.execute("UPDATE NGUYEN_LIEU SET MucTonToiThieu = 0 WHERE MucTonToiThieu IS NULL")
    op.alter_column(
        "NGUYEN_LIEU",
        "MucTonToiThieu",
        existing_type=sa.DECIMAL(precision=18, scale=4),
        nullable=False,
    )
    op.create_check_constraint(CK_MIN_STOCK, "NGUYEN_LIEU", "MucTonToiThieu >= 0")
