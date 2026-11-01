"""MON_AN derives HetNguyenLieu/TrangThai; PHIEU_XUAT_KHO gets NguonXuat.

FR-CAT-27 / FR-INV-10: whether a dish is short of ingredients is derived from the available
quantity of its current recipe, so MON_AN stores neither HetNguyenLieu nor the TrangThai column
generated from it. The two `*_mon` AI views are redefined first so they no longer read the
dropped columns. FR-INV-05: the write-off source moves out of the free-text GhiChu into NguonXuat.

Downgrade restores the columns with HetNguyenLieu = 0 for every dish: the derived value cannot
be reconstructed, and the old code refreshed the flag only on the next stock movement.
"""

import sqlalchemy as sa
from alembic import op

revision = "d01112600002"
down_revision = "d01112600001"
branch_labels = None
depends_on = None

NEW_VIEWS = {
    "vw_ai_quanly_mon": "-- Topic view; only the explicit projected columns are exposed.\n-- TrangThai is derived (FR-CAT-27): MON_AN stores neither HetNguyenLieu nor TrangThai.\nCREATE OR REPLACE VIEW vw_ai_quanly_mon AS\nSELECT m.MaMon, m.TenMon, n.TenNhomMon AS TenNhom,\nCASE\n WHEN m.ChuaCoCongThuc=1 THEN 'Nháp'\n WHEN EXISTS (\n  SELECT 1 FROM CHI_TIET_CONG_THUC ct\n  WHERE ct.MaCongThuc = (\n   SELECT r2.MaCongThuc FROM CONG_THUC r2\n   WHERE r2.MaMon=m.MaMon AND r2.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END)\n   AND r2.TrangThai IN ('Đang áp dụng', 'Chờ áp dụng')\n   ORDER BY r2.BusinessDateApDung DESC, r2.MaCongThuc DESC LIMIT 1\n  )\n  AND ct.DinhLuong>0\n  AND COALESCE((SELECT s.SoLuongKhaDung FROM vw_ai_quanly_ton s WHERE s.MaNguyenLieu=ct.MaNguyenLieu), 0) < ct.DinhLuong\n ) THEN 'Hết nguyên liệu'\n WHEN m.TamDungThuCong=1 THEN 'Tạm dừng phục vụ'\n ELSE 'Hoạt động'\nEND AS TrangThai,\n(SELECT g.GiaBan FROM LICH_SU_GIA_MON g WHERE g.MaMon=m.MaMon\n AND g.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END) AND g.TrangThai IN ('Đang áp dụng','Chờ áp dụng')\n ORDER BY g.BusinessDateApDung DESC,g.MaPhienBanGia DESC LIMIT 1) AS GiaBan\nFROM MON_AN m LEFT JOIN NHOM_MON n ON n.MaNhomMon=m.MaNhomMon WHERE m.DaXoa=0",
    "vw_ai_thungan_mon": "-- Topic view; only the explicit projected columns are exposed.\n-- TrangThai is derived (FR-CAT-27): MON_AN stores neither HetNguyenLieu nor TrangThai.\nCREATE OR REPLACE VIEW vw_ai_thungan_mon AS\nSELECT m.MaMon, m.TenMon, n.TenNhomMon AS TenNhom,\nCASE\n WHEN m.ChuaCoCongThuc=1 THEN 'Nháp'\n WHEN EXISTS (\n  SELECT 1 FROM CHI_TIET_CONG_THUC ct\n  WHERE ct.MaCongThuc = (\n   SELECT r2.MaCongThuc FROM CONG_THUC r2\n   WHERE r2.MaMon=m.MaMon AND r2.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END)\n   AND r2.TrangThai IN ('Đang áp dụng', 'Chờ áp dụng')\n   ORDER BY r2.BusinessDateApDung DESC, r2.MaCongThuc DESC LIMIT 1\n  )\n  AND ct.DinhLuong>0\n  AND COALESCE((SELECT s.SoLuongKhaDung FROM vw_ai_quanly_ton s WHERE s.MaNguyenLieu=ct.MaNguyenLieu), 0) < ct.DinhLuong\n ) THEN 'Hết nguyên liệu'\n WHEN m.TamDungThuCong=1 THEN 'Tạm dừng phục vụ'\n ELSE 'Hoạt động'\nEND AS TrangThai,\n(SELECT g.GiaBan FROM LICH_SU_GIA_MON g WHERE g.MaMon=m.MaMon\n AND g.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END) AND g.TrangThai IN ('Đang áp dụng','Chờ áp dụng')\n ORDER BY g.BusinessDateApDung DESC,g.MaPhienBanGia DESC LIMIT 1) AS GiaBan\nFROM MON_AN m LEFT JOIN NHOM_MON n ON n.MaNhomMon=m.MaNhomMon WHERE m.DaXoa=0",
}

OLD_VIEWS = {
    "vw_ai_quanly_mon": "-- Topic view; only the explicit projected columns are exposed.\nCREATE OR REPLACE VIEW vw_ai_quanly_mon AS\nSELECT m.MaMon, m.TenMon, n.TenNhomMon AS TenNhom, m.TrangThai,\n(SELECT g.GiaBan FROM LICH_SU_GIA_MON g WHERE g.MaMon=m.MaMon\n AND g.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END) AND g.TrangThai IN ('Đang áp dụng','Chờ áp dụng')\n ORDER BY g.BusinessDateApDung DESC,g.MaPhienBanGia DESC LIMIT 1) AS GiaBan\nFROM MON_AN m LEFT JOIN NHOM_MON n ON n.MaNhomMon=m.MaNhomMon WHERE m.DaXoa=0",
    "vw_ai_thungan_mon": "-- Topic view; only the explicit projected columns are exposed.\nCREATE OR REPLACE VIEW vw_ai_thungan_mon AS\nSELECT m.MaMon, m.TenMon, n.TenNhomMon AS TenNhom, m.TrangThai,\n(SELECT g.GiaBan FROM LICH_SU_GIA_MON g WHERE g.MaMon=m.MaMon\n AND g.BusinessDateApDung <= (CASE WHEN CURRENT_TIMESTAMP < COALESCE((SELECT c.ThoiDiemBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc=DATE(CURRENT_TIMESTAMP)), TIMESTAMP(DATE(CURRENT_TIMESTAMP), COALESCE((SELECT c.GioBatDau FROM LICH_GIO_BUSINESS_DATE c WHERE c.NgayHieuLuc<=DATE(CURRENT_TIMESTAMP) ORDER BY c.NgayHieuLuc DESC LIMIT 1), '06:00:00'))) THEN DATE_SUB(DATE(CURRENT_TIMESTAMP), INTERVAL 1 DAY) ELSE DATE(CURRENT_TIMESTAMP) END) AND g.TrangThai IN ('Đang áp dụng','Chờ áp dụng')\n ORDER BY g.BusinessDateApDung DESC,g.MaPhienBanGia DESC LIMIT 1) AS GiaBan\nFROM MON_AN m LEFT JOIN NHOM_MON n ON n.MaNhomMon=m.MaNhomMon WHERE m.DaXoa=0",
}

SOURCES = "'Nguyên liệu', 'Món đã chế biến', 'Kiểm kê'"
CK_SOURCE = op.f("ck_PHIEU_XUAT_KHO_issue_source_valid")


def upgrade() -> None:
    for ddl in NEW_VIEWS.values():
        op.execute(ddl)
    op.drop_column("MON_AN", "TrangThai")
    op.drop_column("MON_AN", "HetNguyenLieu")

    op.add_column(
        "PHIEU_XUAT_KHO",
        sa.Column(
            "NguonXuat",
            sa.String(length=255),
            nullable=False,
            server_default="Nguyên liệu",
        ),
    )
    op.execute(
        "UPDATE PHIEU_XUAT_KHO p SET p.NguonXuat = CASE "
        "WHEN p.MaPhieuKiemKe IS NOT NULL THEN 'Kiểm kê' "
        "WHEN EXISTS (SELECT 1 FROM CHI_TIET_PHIEU_XUAT l "
        "WHERE l.MaPhieuXuat = p.MaPhieuXuat AND l.MaChiTietOrder IS NOT NULL) "
        "THEN 'Món đã chế biến' ELSE 'Nguyên liệu' END"
    )
    # The source used to be stored in GhiChu; keep only genuine notes there.
    op.execute(f"UPDATE PHIEU_XUAT_KHO SET GhiChu = NULL WHERE GhiChu IN ({SOURCES})")
    op.alter_column(
        "PHIEU_XUAT_KHO",
        "NguonXuat",
        existing_type=sa.String(length=255),
        existing_nullable=False,
        server_default=None,
    )
    op.create_check_constraint(CK_SOURCE, "PHIEU_XUAT_KHO", f"NguonXuat IN ({SOURCES})")


def downgrade() -> None:
    op.drop_constraint(CK_SOURCE, "PHIEU_XUAT_KHO", type_="check")
    op.execute("UPDATE PHIEU_XUAT_KHO SET GhiChu = NguonXuat WHERE GhiChu IS NULL")
    op.drop_column("PHIEU_XUAT_KHO", "NguonXuat")

    op.add_column(
        "MON_AN",
        sa.Column("HetNguyenLieu", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.execute(
        "ALTER TABLE MON_AN ADD COLUMN TrangThai VARCHAR(20) "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci GENERATED ALWAYS AS ("
        "CASE WHEN ChuaCoCongThuc=1 THEN 'Nháp' WHEN HetNguyenLieu=1 "
        "THEN 'Hết nguyên liệu' WHEN TamDungThuCong=1 "
        "THEN 'Tạm dừng phục vụ' ELSE 'Hoạt động' END) STORED"
    )
    for ddl in OLD_VIEWS.values():
        op.execute(ddl)
