"""Align the physical schema with report sections 3.2.1 and 3.2.2.

This revision deliberately preserves the Phase-0 migration history.  It is written
for MySQL 8.4: generated columns are recreated explicitly and existing data is
backfilled before obsolete dish-state columns are removed.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c9d3e1f420"
down_revision: str | None = "cd3a65232bee"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Names that are part of the report contract.
    op.execute("ALTER TABLE NHOM_MON RENAME COLUMN TenNhom TO TenNhomMon")
    op.execute("ALTER TABLE LICH_SU_GIA_MON RENAME COLUMN MaLichSuGia TO MaPhienBanGia")
    op.execute("ALTER TABLE LICH_SU_GIA_MON RENAME COLUMN Gia TO GiaBan")
    op.execute("ALTER TABLE CHI_TIET_ORDER RENAME COLUMN MaLichSuGia TO MaPhienBanGia")
    op.execute("ALTER TABLE CHI_TIET_CONG_THUC RENAME COLUMN SoLuong TO DinhLuong")
    op.execute("ALTER TABLE LO_NGUYEN_LIEU RENAME COLUMN MaLo TO MaLoNguyenLieu")
    op.execute("ALTER TABLE GIAO_DICH_KHO RENAME COLUMN SoLuong TO SoLuongThayDoi")
    op.execute("ALTER TABLE GIA_BINH_QUAN_THANG RENAME COLUMN GiaBinhQuan TO DonGiaBinhQuan")
    op.execute("ALTER TABLE NHA_CUNG_CAP RENAME COLUMN MaNhaCungCap TO MaNCC")
    op.execute("ALTER TABLE NHA_CUNG_CAP RENAME COLUMN TenNhaCungCap TO TenNCC")
    op.execute("ALTER TABLE NHA_CUNG_CAP RENAME COLUMN SoDienThoai TO DienThoai")
    op.execute("ALTER TABLE PHIEU_NHAP_KHO RENAME COLUMN MaNhaCungCap TO MaNCC")
    op.execute("ALTER TABLE GIAO_DICH_THANH_TOAN RENAME COLUMN MaGiaoDich TO MaGiaoDichTT")
    op.execute("ALTER TABLE GIAO_DICH_THANH_TOAN RENAME COLUMN HanQr TO ThoiDiemHetHan")
    op.execute(
        "ALTER TABLE GIAO_DICH_THANH_TOAN RENAME COLUMN MaThamChieuNganHang TO MaGiaoDichNganHang"
    )
    op.execute("ALTER TABLE GIAO_DICH_THANH_TOAN RENAME COLUMN ChungTuDoiSoat TO AnhChungTu")
    op.execute("ALTER TABLE LICH_SU_DOI_BAN RENAME COLUMN MaLichSu TO MaLichSuDoiBan")
    op.execute("ALTER TABLE LICH_SU_DOI_BAN RENAME COLUMN NgayTao TO ThoiDiem")

    # MON_AN: 'Nháp' is now a database state, not an application inference.
    op.execute("ALTER TABLE MON_AN DROP COLUMN TrangThai")
    op.add_column(
        "MON_AN",
        sa.Column("ChuaCoCongThuc", sa.Boolean(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column(
        "MON_AN",
        sa.Column("HetNguyenLieu", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.execute(
        "UPDATE MON_AN m SET ChuaCoCongThuc = NOT EXISTS "
        "(SELECT 1 FROM CONG_THUC c WHERE c.MaMon=m.MaMon AND c.TrangThai IN ('Hiệu lực', 'Đang áp dụng')), "
        "HetNguyenLieu = (m.HetNLThuCong = 1 OR m.HetNLTuDong = 1)"
    )
    op.drop_column("MON_AN", "AnThuCong")
    op.drop_column("MON_AN", "HetNLThuCong")
    op.drop_column("MON_AN", "HetNLTuDong")
    op.add_column(
        "MON_AN",
        sa.Column(
            "TrangThai",
            sa.String(20),
            sa.Computed(
                "CASE WHEN ChuaCoCongThuc=1 THEN 'Nháp' WHEN HetNguyenLieu=1 THEN 'Hết nguyên liệu' ELSE 'Hoạt động' END",
                persisted=True,
            ),
        ),
    )

    # Additional report attributes. Defaults retain valid existing rows.
    for table, column in (
        ("NHOM_MON", sa.Column("NgayXoa", sa.DateTime(), nullable=True)),
        ("NHA_CUNG_CAP", sa.Column("NguoiLienHe", sa.String(100), nullable=True)),
        ("NHA_CUNG_CAP", sa.Column("Email", sa.String(255), nullable=True)),
        ("NHA_CUNG_CAP", sa.Column("DiaChi", sa.String(255), nullable=True)),
        ("BAN", sa.Column("KhuVuc", sa.String(100), nullable=True)),
        ("BAN", sa.Column("SoChoNgoi", sa.Integer(), nullable=True)),
        (
            "LICH_SU_GIA_MON",
            sa.Column(
                "ThoiDiemTao",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        ),
        (
            "CONG_THUC",
            sa.Column("SoPhienBan", sa.Integer(), nullable=False, server_default=sa.text("1")),
        ),
        (
            "CONG_THUC",
            sa.Column(
                "ThoiDiemTao",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        ),
        (
            "ORDER",
            sa.Column("TongTien", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("0")),
        ),
        ("ORDER", sa.Column("ThoiDiemDong", sa.DateTime(), nullable=True)),
        ("CHI_TIET_ORDER", sa.Column("ThanhTien", sa.DECIMAL(18, 4), nullable=True)),
        (
            "CHI_TIET_ORDER",
            sa.Column(
                "ThoiDiemThem",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        ),
        ("LICH_SU_DOI_BAN", sa.Column("NguoiThucHien", sa.BigInteger(), nullable=True)),
        (
            "PHIEU_NHAP_KHO",
            sa.Column("TongTien", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("0")),
        ),
        ("PHIEU_NHAP_KHO", sa.Column("GhiChu", sa.String(500), nullable=True)),
        ("CHI_TIET_PHIEU_NHAP", sa.Column("DonViMuaGoc", sa.String(20), nullable=True)),
        (
            "CHI_TIET_PHIEU_NHAP",
            sa.Column("HeSoQuyDoi", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("1")),
        ),
        (
            "CHI_TIET_PHIEU_NHAP",
            sa.Column("ThanhTien", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("0")),
        ),
        ("LO_NGUYEN_LIEU", sa.Column("HanSuDung", sa.Date(), nullable=True)),
        (
            "LO_NGUYEN_LIEU",
            sa.Column(
                "SoLuongNhap", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("0")
            ),
        ),
        (
            "LO_NGUYEN_LIEU",
            sa.Column("DonGia", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("0")),
        ),
        ("PHIEU_XUAT_KHO", sa.Column("NgayXuat", sa.DateTime(), nullable=True)),
        ("PHIEU_XUAT_KHO", sa.Column("NguoiLap", sa.BigInteger(), nullable=True)),
        ("PHIEU_XUAT_KHO", sa.Column("GhiChu", sa.String(500), nullable=True)),
        ("PHIEU_KIEM_KE", sa.Column("NguoiThucHien", sa.BigInteger(), nullable=True)),
        ("PHIEU_KIEM_KE", sa.Column("GhiChu", sa.String(500), nullable=True)),
        (
            "GIAO_DICH_KHO",
            sa.Column(
                "TonSauGiaoDich", sa.DECIMAL(18, 4), nullable=False, server_default=sa.text("0")
            ),
        ),
        ("PHIEN_CHAT_AI", sa.Column("MaVaiTro", sa.String(20), nullable=True)),
        ("PHIEN_CHAT_AI", sa.Column("ThoiDiemKetThuc", sa.DateTime(), nullable=True)),
    ):
        op.add_column(table, column)
    op.execute("ALTER TABLE PHIEN_CHAT_AI RENAME COLUMN NgayTao TO ThoiDiemBatDau")
    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("MaQR", sa.String(500), nullable=True))
    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("ThoiDiemTaoQR", sa.DateTime(), nullable=True))
    op.add_column(
        "GIAO_DICH_THANH_TOAN", sa.Column("MaGiaoDichCong", sa.String(100), nullable=True)
    )
    op.add_column(
        "GIAO_DICH_THANH_TOAN", sa.Column("NoiDungWebhook", sa.String(2000), nullable=True)
    )
    op.add_column("HOA_DON", sa.Column("MaGiaoDichThanhToan", sa.BigInteger(), nullable=True))
    op.add_column("HOA_DON", sa.Column("SoHoaDon", sa.String(50), nullable=True))
    op.add_column("HOA_DON", sa.Column("PhuongThucThanhToan", sa.String(20), nullable=True))
    op.add_column("HOA_DON", sa.Column("NguoiLap", sa.BigInteger(), nullable=True))

    op.execute("UPDATE CHI_TIET_ORDER SET ThanhTien = SoLuong * DonGia")
    op.execute(
        "UPDATE `ORDER` o SET TongTien = COALESCE((SELECT SUM(ThanhTien) FROM CHI_TIET_ORDER c WHERE c.MaOrder=o.MaOrder), 0)"
    )
    op.execute(
        "UPDATE PHIEU_NHAP_KHO p SET TongTien = COALESCE((SELECT SUM(SoLuong * DonGia) FROM CHI_TIET_PHIEU_NHAP c WHERE c.MaPhieuNhap=p.MaPhieuNhap), 0)"
    )
    op.execute("UPDATE CHI_TIET_PHIEU_NHAP SET ThanhTien = SoLuong * DonGia")
    op.execute("UPDATE LO_NGUYEN_LIEU SET SoLuongNhap = SoLuongConLai")
    op.execute(
        "UPDATE LO_NGUYEN_LIEU l LEFT JOIN CHI_TIET_PHIEU_NHAP c ON c.MaChiTietNhap=l.MaChiTietNhap SET l.DonGia=COALESCE(c.DonGia, 0)"
    )
    op.execute(
        "ALTER TABLE CAU_HINH_HE_THONG MODIFY COLUMN NguongTonMacDinh DECIMAL(18,4) NOT NULL"
    )
    op.execute("UPDATE LICH_SU_GIA_MON SET TrangThai='Chờ áp dụng' WHERE TrangThai='Nháp'")
    op.execute("UPDATE LICH_SU_GIA_MON SET TrangThai='Đang áp dụng' WHERE TrangThai='Hiệu lực'")
    op.execute("UPDATE CONG_THUC SET TrangThai='Chờ áp dụng' WHERE TrangThai='Nháp'")
    op.execute("UPDATE CONG_THUC SET TrangThai='Đang áp dụng' WHERE TrangThai='Hiệu lực'")


def downgrade() -> None:
    raise NotImplementedError(
        "This data-preserving schema alignment is intentionally forward-only."
    )
