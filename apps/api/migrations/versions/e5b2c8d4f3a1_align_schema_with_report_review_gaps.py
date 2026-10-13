"""Close the gaps between the physical schema and the report (review of 2026-10).

Revision ID: e5b2c8d4f3a1
Revises: 4e2d9f31a6bc

What it changes (MySQL 8.4):

* Foreign keys the report names but the schema lacked: LICH_SU_DOI_BAN.NguoiThucHien,
  PHIEU_XUAT_KHO.NguoiLap, PHIEU_KIEM_KE.NguoiThucHien, HOA_DON.MaGiaoDichThanhToan,
  HOA_DON.NguoiLap, PHIEN_CHAT_AI.MaVaiTro; ON DELETE/UPDATE RESTRICT made explicit on
  NHAT_KY_HE_THONG.MaNguoiDung and TRUY_VAN_AI.MaPhien (was CASCADE).
* Two foreign keys renamed to follow their renamed columns (fk_CHI_TIET_ORDER_MaPhienBanGia,
  fk_PHIEU_NHAP_KHO_MaNCC), so every constraint name matches the models.
* UNIQUE: VAI_TRO.TenVaiTro, HOA_DON.SoHoaDon, GIAO_DICH_THANH_TOAN.MaGiaoDichCong and
  MaGiaoDichNganHang.
* CHECK: the positive-quantity/price rules of the attribute tables, the configuration
  ranges, and the non-negative AI usage counters.
* New columns: MON_AN.TamDungThuCong (and the TrangThai expression that uses it),
  BAN.MaOrderDangPhucVu, PHIEU_XUAT_KHO.NguonXuat/MaPhieuKiemKe,
  CHI_TIET_PHIEU_XUAT.MaChiTietOrder/SoSuatHuy, the payment-exception columns of
  GIAO_DICH_THANH_TOAN, and the model/token/cost columns of TRUY_VAN_AI.
* NGUYEN_LIEU.MucTonToiThieu becomes nullable: NULL means "use the system default".
* GIAO_DICH_THANH_TOAN.TrangThai widens to 30 characters (the report's longest state has 25).
* Data: the payment/order states 'Chờ đối soát' and 'Tranh chấp' become the report's single
  'Chờ xác minh thanh toán'; every lot status is recomputed from its expiry date and quantity
  (cancelled receipts' lots read 'Đã dùng hết'); a MucTonToiThieu of 0 (which used to mean
  "unset") becomes NULL.

Not reversible without loss: the downgrade maps every 'Chờ xác minh thanh toán' back to
'Chờ đối soát', and cannot recover which dishes were hidden by hand (see below).
HetNguyenLieu used to be settable by hand; it is now derived, and any hand-set value is
overwritten the next time a stock event recomputes the dish.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e5b2c8d4f3a1"
down_revision: str | None = "4e2d9f31a6bc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (table, constraint, condition) added in upgrade() and dropped in downgrade().
CHECKS: tuple[tuple[str, str, str], ...] = (
    ("LICH_SU_GIA_MON", "price_positive", "GiaBan > 0"),
    ("CHI_TIET_CONG_THUC", "quantity_positive", "DinhLuong > 0"),
    ("CHI_TIET_ORDER", "quantity_positive", "SoLuong > 0"),
    ("CHI_TIET_PHIEU_NHAP", "quantity_positive", "SoLuong > 0"),
    ("CHI_TIET_PHIEU_NHAP", "conversion_factor_positive", "HeSoQuyDoi > 0"),
    ("LO_NGUYEN_LIEU", "received_quantity_positive", "SoLuongNhap > 0"),
    ("LO_NGUYEN_LIEU", "remaining_quantity_non_negative", "SoLuongConLai >= 0"),
    ("CHI_TIET_PHIEU_XUAT", "quantity_positive", "SoLuong > 0"),
    ("CHI_TIET_PHIEU_XUAT", "servings_positive", "SoSuatHuy IS NULL OR SoSuatHuy > 0"),
    (
        "CHI_TIET_PHIEU_XUAT",
        "dish_reference_complete",
        "(MaChiTietOrder IS NULL) = (SoSuatHuy IS NULL)",
    ),
    (
        "PHIEU_XUAT_KHO",
        "source_known",
        "NguonXuat IN ('Nguyên liệu', 'Món đã chế biến', 'Kiểm kê')",
    ),
    (
        "PHIEU_XUAT_KHO",
        "stocktake_source_matches_reference",
        "(NguonXuat = 'Kiểm kê') = (MaPhieuKiemKe IS NOT NULL)",
    ),
    ("CAU_HINH_HE_THONG", "default_stock_threshold_non_negative", "NguongTonMacDinh >= 0"),
    ("CAU_HINH_HE_THONG", "expiry_warning_days_positive", "SoNgayCanhBaoHetHan > 0"),
    ("CAU_HINH_HE_THONG", "ai_daily_question_quota_positive", "SoCauHoiAIMoiNgay > 0"),
    ("CAU_HINH_HE_THONG", "reservation_hold_minutes_positive", "ThoiGianGiuChoPhut > 0"),
    ("TRUY_VAN_AI", "input_tokens_non_negative", "TokenDauVao IS NULL OR TokenDauVao >= 0"),
    ("TRUY_VAN_AI", "output_tokens_non_negative", "TokenDauRa IS NULL OR TokenDauRa >= 0"),
    ("TRUY_VAN_AI", "cost_usd_non_negative", "ChiPhiUSD IS NULL OR ChiPhiUSD >= 0"),
    ("TRUY_VAN_AI", "call_count_non_negative", "SoLanGoi IS NULL OR SoLanGoi >= 0"),
)

# (table, constraint, columns) added in upgrade() and dropped in downgrade().
UNIQUES: tuple[tuple[str, str, list[str]], ...] = (
    ("VAI_TRO", "uq_VAI_TRO_TenVaiTro", ["TenVaiTro"]),
    ("HOA_DON", "uq_HOA_DON_SoHoaDon", ["SoHoaDon"]),
    ("GIAO_DICH_THANH_TOAN", "uq_GIAO_DICH_THANH_TOAN_MaGiaoDichCong", ["MaGiaoDichCong"]),
    (
        "GIAO_DICH_THANH_TOAN",
        "uq_GIAO_DICH_THANH_TOAN_MaGiaoDichNganHang",
        ["MaGiaoDichNganHang"],
    ),
)

# (name, source table, source column, referenced "table.column") for the new foreign keys.
FOREIGN_KEYS: tuple[tuple[str, str, str, str], ...] = (
    (
        "fk_LICH_SU_DOI_BAN_NguoiThucHien",
        "LICH_SU_DOI_BAN",
        "NguoiThucHien",
        "NGUOI_DUNG.MaNguoiDung",
    ),
    ("fk_PHIEU_XUAT_KHO_NguoiLap", "PHIEU_XUAT_KHO", "NguoiLap", "NGUOI_DUNG.MaNguoiDung"),
    (
        "fk_PHIEU_KIEM_KE_NguoiThucHien",
        "PHIEU_KIEM_KE",
        "NguoiThucHien",
        "NGUOI_DUNG.MaNguoiDung",
    ),
    ("fk_HOA_DON_NguoiLap", "HOA_DON", "NguoiLap", "NGUOI_DUNG.MaNguoiDung"),
    (
        "fk_HOA_DON_MaGiaoDichThanhToan",
        "HOA_DON",
        "MaGiaoDichThanhToan",
        "GIAO_DICH_THANH_TOAN.MaGiaoDichTT",
    ),
    ("fk_PHIEN_CHAT_AI_MaVaiTro", "PHIEN_CHAT_AI", "MaVaiTro", "VAI_TRO.MaVaiTro"),
)

DISH_STATUS_NEW = (
    "CASE WHEN ChuaCoCongThuc=1 THEN 'Nháp' WHEN HetNguyenLieu=1 THEN 'Hết nguyên liệu' "
    "WHEN TamDungThuCong=1 THEN 'Tạm dừng phục vụ' ELSE 'Hoạt động' END"
)
DISH_STATUS_OLD = (
    "CASE WHEN ChuaCoCongThuc=1 THEN 'Nháp' WHEN HetNguyenLieu=1 THEN 'Hết nguyên liệu' "
    "ELSE 'Hoạt động' END"
)

# Constraint names left behind by the column renames of b7c9d3e1f420: (old, new, table, column,
# referenced "table.column", on delete).
RENAMED_FOREIGN_KEYS: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "fk_CHI_TIET_ORDER_MaLichSuGia",
        "fk_CHI_TIET_ORDER_MaPhienBanGia",
        "CHI_TIET_ORDER",
        "MaPhienBanGia",
        "LICH_SU_GIA_MON.MaPhienBanGia",
        "RESTRICT",
    ),
    (
        "fk_PHIEU_NHAP_KHO_MaNhaCungCap",
        "fk_PHIEU_NHAP_KHO_MaNCC",
        "PHIEU_NHAP_KHO",
        "MaNCC",
        "NHA_CUNG_CAP.MaNCC",
        "RESTRICT",
    ),
)

MOVEMENT_CHECK = (
    "((LoaiGiaoDich = 'Nhập' AND MaChiTietNhap IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Trừ tự động' AND MaChiTietOrder IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Hoàn kho' AND MaChiTietOrder IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Xuất thủ công' AND MaChiTietXuat IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Điều chỉnh kiểm kê' AND MaChiTietKiemKe IS NOT NULL))"
)


def _ck(table: str, name: str) -> str:
    return op.f(f"ck_{table}_{name}")


def upgrade() -> None:
    # --- states: the report has one "waiting for verification" state -------------------
    # The column is widened first: the report's longest state has 25 characters.
    op.alter_column(
        "GIAO_DICH_THANH_TOAN",
        "TrangThai",
        existing_type=sa.String(20),
        type_=sa.String(30),
        existing_nullable=False,
    )
    for table in ("GIAO_DICH_THANH_TOAN", "`ORDER`"):
        op.execute(
            f"UPDATE {table} SET TrangThai = 'Chờ xác minh thanh toán' "
            "WHERE TrangThai IN ('Chờ đối soát', 'Tranh chấp')"
        )

    # --- data repair that the new constraints would otherwise reject -------------------
    # Columns added without a foreign key could only hold ids that never existed.
    op.execute(
        "UPDATE LICH_SU_DOI_BAN SET NguoiThucHien = NULL WHERE NguoiThucHien IS NOT NULL "
        "AND NguoiThucHien NOT IN (SELECT MaNguoiDung FROM NGUOI_DUNG)"
    )
    op.execute(
        "UPDATE PHIEU_XUAT_KHO SET NguoiLap = NULL WHERE NguoiLap IS NOT NULL "
        "AND NguoiLap NOT IN (SELECT MaNguoiDung FROM NGUOI_DUNG)"
    )
    op.execute(
        "UPDATE PHIEU_KIEM_KE SET NguoiThucHien = NULL WHERE NguoiThucHien IS NOT NULL "
        "AND NguoiThucHien NOT IN (SELECT MaNguoiDung FROM NGUOI_DUNG)"
    )
    op.execute(
        "UPDATE HOA_DON SET NguoiLap = NULL WHERE NguoiLap IS NOT NULL "
        "AND NguoiLap NOT IN (SELECT MaNguoiDung FROM NGUOI_DUNG)"
    )
    op.execute(
        "UPDATE HOA_DON SET MaGiaoDichThanhToan = NULL WHERE MaGiaoDichThanhToan IS NOT NULL "
        "AND MaGiaoDichThanhToan NOT IN (SELECT MaGiaoDichTT FROM GIAO_DICH_THANH_TOAN)"
    )
    # A session's role at the time of the chat is the owner's role (FR-AI-05).
    op.execute(
        "UPDATE PHIEN_CHAT_AI p JOIN NGUOI_DUNG u ON u.MaNguoiDung = p.MaNguoiDung "
        "SET p.MaVaiTro = u.MaVaiTro WHERE p.MaVaiTro IS NULL"
    )
    op.execute(
        "UPDATE LO_NGUYEN_LIEU l LEFT JOIN CHI_TIET_PHIEU_NHAP c "
        "ON c.MaChiTietNhap = l.MaChiTietNhap "
        "SET l.SoLuongNhap = COALESCE(c.SoLuong, GREATEST(l.SoLuongConLai, 0.0001)) "
        "WHERE l.SoLuongNhap <= 0"
    )
    # Lot statuses are derived from expiry and quantity (FR-INV-14). The application keeps
    # them current from now on; this brings the stored ones up to date at deployment, so the
    # AI views, which filter on TrangThai, are right before the first stock operation.
    op.execute(
        "UPDATE LO_NGUYEN_LIEU SET TrangThai = CASE "
        "WHEN SoLuongConLai <= 0 THEN 'Đã dùng hết' "
        "WHEN HanSuDung IS NULL THEN 'Còn hạn' "
        "WHEN HanSuDung < CURRENT_DATE THEN 'Hết hạn' "
        "WHEN HanSuDung <= DATE_ADD(CURRENT_DATE, INTERVAL "
        "(SELECT SoNgayCanhBaoHetHan FROM CAU_HINH_HE_THONG ORDER BY MaCauHinh LIMIT 1) DAY) "
        "THEN 'Sắp hết hạn' ELSE 'Còn hạn' END"
    )

    # --- unique constraints -----------------------------------------------------------
    for table, name, columns in UNIQUES:
        op.create_unique_constraint(op.f(name), table, columns)

    # --- new columns -------------------------------------------------------------------
    op.add_column(
        "MON_AN",
        sa.Column("TamDungThuCong", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.drop_column("MON_AN", "TrangThai")
    op.add_column(
        "MON_AN",
        sa.Column("TrangThai", sa.String(20), sa.Computed(DISH_STATUS_NEW, persisted=True)),
    )

    op.drop_constraint(_ck("NGUYEN_LIEU", "min_stock_non_negative"), "NGUYEN_LIEU", type_="check")
    op.alter_column("NGUYEN_LIEU", "MucTonToiThieu", existing_type=sa.DECIMAL(18, 4), nullable=True)
    op.execute("UPDATE NGUYEN_LIEU SET MucTonToiThieu = NULL WHERE MucTonToiThieu = 0")
    op.create_check_constraint(
        _ck("NGUYEN_LIEU", "min_stock_non_negative"),
        "NGUYEN_LIEU",
        "MucTonToiThieu IS NULL OR MucTonToiThieu >= 0",
    )

    op.add_column("BAN", sa.Column("MaOrderDangPhucVu", sa.BigInteger(), nullable=True))
    op.execute(
        "UPDATE BAN b SET b.MaOrderDangPhucVu = (SELECT MAX(o.MaOrder) FROM `ORDER` o "
        "WHERE o.MaBan = b.MaBan AND o.TrangThai IN ('Đang mở', 'Chờ xác nhận thanh toán', "
        "'Chờ xác minh thanh toán')) WHERE b.TrangThai = 'Đang phục vụ'"
    )
    op.create_foreign_key(
        op.f("fk_BAN_MaOrderDangPhucVu"),
        "BAN",
        "ORDER",
        ["MaOrderDangPhucVu"],
        ["MaOrder"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )

    op.add_column(
        "PHIEU_XUAT_KHO",
        sa.Column(
            "NguonXuat", sa.String(30), nullable=False, server_default=sa.text("'Nguyên liệu'")
        ),
    )
    op.add_column("PHIEU_XUAT_KHO", sa.Column("MaPhieuKiemKe", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        op.f("fk_PHIEU_XUAT_KHO_MaPhieuKiemKe"),
        "PHIEU_XUAT_KHO",
        "PHIEU_KIEM_KE",
        ["MaPhieuKiemKe"],
        ["MaPhieuKiemKe"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )
    op.add_column(
        "CHI_TIET_PHIEU_XUAT", sa.Column("MaChiTietOrder", sa.BigInteger(), nullable=True)
    )
    op.add_column("CHI_TIET_PHIEU_XUAT", sa.Column("SoSuatHuy", sa.Integer(), nullable=True))
    op.create_foreign_key(
        op.f("fk_CHI_TIET_PHIEU_XUAT_MaChiTietOrder"),
        "CHI_TIET_PHIEU_XUAT",
        "CHI_TIET_ORDER",
        ["MaChiTietOrder"],
        ["MaChiTietOrder"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )

    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("TrangThaiNgoaiLe", sa.String(30)))
    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("SoTienNgoaiLe", sa.DECIMAL(18, 4)))
    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("MaThamChieuHoan", sa.String(100)))
    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("ThoiDiemXuLyNgoaiLe", sa.DateTime()))
    op.add_column("GIAO_DICH_THANH_TOAN", sa.Column("NguoiXuLyNgoaiLe", sa.BigInteger()))
    op.create_foreign_key(
        op.f("fk_GIAO_DICH_THANH_TOAN_NguoiXuLyNgoaiLe"),
        "GIAO_DICH_THANH_TOAN",
        "NGUOI_DUNG",
        ["NguoiXuLyNgoaiLe"],
        ["MaNguoiDung"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )

    op.add_column("TRUY_VAN_AI", sa.Column("ModelPhienBan", sa.String(100)))
    op.add_column("TRUY_VAN_AI", sa.Column("TokenDauVao", sa.Integer()))
    op.add_column("TRUY_VAN_AI", sa.Column("TokenDauRa", sa.Integer()))
    op.add_column("TRUY_VAN_AI", sa.Column("ChiPhiUSD", sa.DECIMAL(12, 6)))
    op.add_column("TRUY_VAN_AI", sa.Column("SoLanGoi", sa.Integer()))

    # --- foreign keys --------------------------------------------------------------------
    for name, table, column, target in FOREIGN_KEYS:
        ref_table, ref_column = target.split(".")
        op.create_foreign_key(
            op.f(name),
            table,
            ref_table,
            [column],
            [ref_column],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        )
    # Restating the actions makes them explicit; TRUY_VAN_AI also stops cascading (append-only log).
    for constraint, table, column, ref_table, ref_column in (
        (
            "fk_NHAT_KY_HE_THONG_MaNguoiDung",
            "NHAT_KY_HE_THONG",
            "MaNguoiDung",
            "NGUOI_DUNG",
            "MaNguoiDung",
        ),
        ("fk_TRUY_VAN_AI_MaPhien", "TRUY_VAN_AI", "MaPhien", "PHIEN_CHAT_AI", "MaPhien"),
    ):
        op.drop_constraint(constraint, table, type_="foreignkey")
        op.create_foreign_key(
            op.f(constraint),
            table,
            ref_table,
            [column],
            [ref_column],
            ondelete="RESTRICT",
            onupdate="RESTRICT",
        )

    for old, new, table, column, target, ondelete in RENAMED_FOREIGN_KEYS:
        ref_table, ref_column = target.split(".")
        op.drop_constraint(old, table, type_="foreignkey")
        op.create_foreign_key(
            op.f(new),
            table,
            ref_table,
            [column],
            [ref_column],
            ondelete=ondelete,
            onupdate="RESTRICT",
        )

    # --- check constraints -------------------------------------------------------------
    op.drop_constraint(
        _ck("GIAO_DICH_KHO", "movement_source_matches_kind"), "GIAO_DICH_KHO", type_="check"
    )
    op.create_check_constraint(
        _ck("GIAO_DICH_KHO", "movement_source_matches_kind"), "GIAO_DICH_KHO", MOVEMENT_CHECK
    )
    for table, name, condition in CHECKS:
        op.create_check_constraint(_ck(table, name), table, condition)


def downgrade() -> None:
    for table, name, _ in reversed(CHECKS):
        op.drop_constraint(_ck(table, name), table, type_="check")

    op.drop_constraint("fk_TRUY_VAN_AI_MaPhien", "TRUY_VAN_AI", type_="foreignkey")
    op.drop_constraint("fk_NHAT_KY_HE_THONG_MaNguoiDung", "NHAT_KY_HE_THONG", type_="foreignkey")
    op.create_foreign_key(
        op.f("fk_NHAT_KY_HE_THONG_MaNguoiDung"),
        "NHAT_KY_HE_THONG",
        "NGUOI_DUNG",
        ["MaNguoiDung"],
        ["MaNguoiDung"],
    )
    op.create_foreign_key(
        op.f("fk_TRUY_VAN_AI_MaPhien"),
        "TRUY_VAN_AI",
        "PHIEN_CHAT_AI",
        ["MaPhien"],
        ["MaPhien"],
        ondelete="CASCADE",
        onupdate="RESTRICT",
    )
    for name, table, _, _ in reversed(FOREIGN_KEYS):
        op.drop_constraint(name, table, type_="foreignkey")
    for old, new, table, column, target, ondelete in RENAMED_FOREIGN_KEYS:
        ref_table, ref_column = target.split(".")
        op.drop_constraint(new, table, type_="foreignkey")
        op.create_foreign_key(
            op.f(old),
            table,
            ref_table,
            [column],
            [ref_column],
            ondelete=ondelete,
            onupdate="RESTRICT",
        )

    for table in ("GIAO_DICH_THANH_TOAN", "`ORDER`"):
        op.execute(
            f"UPDATE {table} SET TrangThai = 'Chờ đối soát' "
            "WHERE TrangThai = 'Chờ xác minh thanh toán'"
        )

    for column in ("SoLanGoi", "ChiPhiUSD", "TokenDauRa", "TokenDauVao", "ModelPhienBan"):
        op.drop_column("TRUY_VAN_AI", column)

    op.drop_constraint(
        "fk_GIAO_DICH_THANH_TOAN_NguoiXuLyNgoaiLe", "GIAO_DICH_THANH_TOAN", type_="foreignkey"
    )
    for column in (
        "NguoiXuLyNgoaiLe",
        "ThoiDiemXuLyNgoaiLe",
        "MaThamChieuHoan",
        "SoTienNgoaiLe",
        "TrangThaiNgoaiLe",
    ):
        op.drop_column("GIAO_DICH_THANH_TOAN", column)
    op.alter_column(
        "GIAO_DICH_THANH_TOAN",
        "TrangThai",
        existing_type=sa.String(30),
        type_=sa.String(20),
        existing_nullable=False,
    )

    op.drop_constraint(
        "fk_CHI_TIET_PHIEU_XUAT_MaChiTietOrder", "CHI_TIET_PHIEU_XUAT", type_="foreignkey"
    )
    op.drop_column("CHI_TIET_PHIEU_XUAT", "SoSuatHuy")
    op.drop_column("CHI_TIET_PHIEU_XUAT", "MaChiTietOrder")
    op.drop_constraint("fk_PHIEU_XUAT_KHO_MaPhieuKiemKe", "PHIEU_XUAT_KHO", type_="foreignkey")
    op.drop_column("PHIEU_XUAT_KHO", "MaPhieuKiemKe")
    op.drop_column("PHIEU_XUAT_KHO", "NguonXuat")

    op.drop_constraint("fk_BAN_MaOrderDangPhucVu", "BAN", type_="foreignkey")
    op.drop_column("BAN", "MaOrderDangPhucVu")

    op.drop_constraint(_ck("NGUYEN_LIEU", "min_stock_non_negative"), "NGUYEN_LIEU", type_="check")
    op.execute("UPDATE NGUYEN_LIEU SET MucTonToiThieu = 0 WHERE MucTonToiThieu IS NULL")
    op.alter_column(
        "NGUYEN_LIEU", "MucTonToiThieu", existing_type=sa.DECIMAL(18, 4), nullable=False
    )
    op.create_check_constraint(
        _ck("NGUYEN_LIEU", "min_stock_non_negative"), "NGUYEN_LIEU", "MucTonToiThieu >= 0"
    )

    op.drop_column("MON_AN", "TrangThai")
    op.add_column(
        "MON_AN",
        sa.Column("TrangThai", sa.String(20), sa.Computed(DISH_STATUS_OLD, persisted=True)),
    )
    op.drop_column("MON_AN", "TamDungThuCong")

    for table, name, _ in reversed(UNIQUES):
        op.drop_constraint(name, table, type_="unique")
