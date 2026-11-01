"""Column types follow the physical design (report §4.2.2, document 04 part F).

* DATETIME -> DATETIME(3): millisecond precision for every timestamp.
* Quantities, conversion factors and stock levels widen to DECIMAL(18,6); money narrows to
  DECIMAL(18,2).
* CHI_TIET_ORDER.SoLuong narrows from BIGINT to INT.

Narrowing can lose data, so it is never done blindly: every money column is checked first and the
migration aborts, naming the column, if any stored value has a digit beyond the new scale.
`GiaVonUocTinh` and `DonGiaBinhQuan` are derived estimates that the application recomputes, so
those two are rounded half up instead (MySQL ROUND). Defaults and nullability are read back from
the live column so they are preserved, with CURRENT_TIMESTAMP gaining the matching precision.

Downgrade restores the previous types. Money digits narrowed away here are not recoverable, and
quantities stored with more than four decimals are rounded when they go back to DECIMAL(18,4).
"""

import re

import sqlalchemy as sa
from alembic import op

revision = "d01112600005"
down_revision = "d01112600004"
branch_labels = None
depends_on = None

COLUMNS: dict[str, dict[str, str]] = {
    "NGUOI_DUNG": {"NgayTao": "DATETIME(3)"},
    "CAU_HINH_HE_THONG": {"NguongTonMacDinh": "DECIMAL(18,6)"},
    "NHAT_KY_HE_THONG": {"ThoiDiem": "DATETIME(3)"},
    "NHOM_MON": {"NgayXoa": "DATETIME(3)"},
    "LICH_SU_GIA_MON": {
        "GiaBan": "DECIMAL(18,2)",
        "ThoiDiemHetHieuLuc": "DATETIME(3)",
        "ThoiDiemHieuLuc": "DATETIME(3)",
        "ThoiDiemTao": "DATETIME(3)",
    },
    "CONG_THUC": {
        "ThoiDiemHetHieuLuc": "DATETIME(3)",
        "ThoiDiemHieuLuc": "DATETIME(3)",
        "ThoiDiemTao": "DATETIME(3)",
    },
    "CHI_TIET_CONG_THUC": {"DinhLuong": "DECIMAL(18,6)"},
    "NGUYEN_LIEU": {"MucTonToiThieu": "DECIMAL(18,6)", "SoLuongTon": "DECIMAL(18,6)"},
    "ORDER": {
        "TongTien": "DECIMAL(18,2)",
        "NgayCapNhat": "DATETIME(3)",
        "NgayTao": "DATETIME(3)",
        "ThoiDiemDong": "DATETIME(3)",
    },
    "CHI_TIET_ORDER": {
        "ThoiDiemThem": "DATETIME(3)",
        "SoLuong": "INT",
        "DonGia": "DECIMAL(18,2)",
        "ThanhTien": "DECIMAL(18,2)",
    },
    "LICH_SU_DOI_BAN": {"ThoiDiem": "DATETIME(3)"},
    "HOA_DON": {"ThoiDiemXuat": "DATETIME(3)", "TongTien": "DECIMAL(18,2)"},
    "GIAO_DICH_THANH_TOAN": {
        "NgayTao": "DATETIME(3)",
        "ThoiDiemHetHan": "DATETIME(3)",
        "ThoiDiemTaoQR": "DATETIME(3)",
        "SoTien": "DECIMAL(18,2)",
    },
    "PHIEU_BEP": {
        "HanKhoaIn": "DATETIME(3)",
        "LanThuTiepTheo": "DATETIME(3)",
        "NgayTao": "DATETIME(3)",
        "ThoiDiemIn": "DATETIME(3)",
    },
    "PHIEU_NHAP_KHO": {"NgayNhap": "DATETIME(3)", "TongTien": "DECIMAL(18,2)"},
    "CHI_TIET_PHIEU_NHAP": {
        "HeSoQuyDoi": "DECIMAL(18,6)",
        "SoLuong": "DECIMAL(18,6)",
        "DonGia": "DECIMAL(18,2)",
        "ThanhTien": "DECIMAL(18,2)",
    },
    "LO_NGUYEN_LIEU": {
        "NgayNhap": "DATETIME(3)",
        "DonGia": "DECIMAL(18,2)",
        "SoLuongConLai": "DECIMAL(18,6)",
        "SoLuongNhap": "DECIMAL(18,6)",
    },
    "PHIEU_XUAT_KHO": {"NgayTao": "DATETIME(3)", "NgayXuat": "DATETIME(3)"},
    "CHI_TIET_PHIEU_XUAT": {"SoLuong": "DECIMAL(18,6)", "GiaVonUocTinh": "DECIMAL(18,2)"},
    "PHIEU_KIEM_KE": {"NgayKiemKe": "DATETIME(3)"},
    "CHI_TIET_KIEM_KE": {
        "ChenhLech": "DECIMAL(18,6)",
        "TonHeThong": "DECIMAL(18,6)",
        "TonThucTe": "DECIMAL(18,6)",
    },
    "GIAO_DICH_KHO": {
        "SoLuongThayDoi": "DECIMAL(18,6)",
        "TonSauGiaoDich": "DECIMAL(18,6)",
        "ThoiDiem": "DATETIME(3)",
    },
    "GIA_BINH_QUAN_THANG": {
        "DonGiaBinhQuan": "DECIMAL(18,2)",
        "TongSoLuongNhap": "DECIMAL(18,6)",
        "ThoiDiemTinh": "DATETIME(3)",
    },
    "PHIEN_CHAT_AI": {"ThoiDiemBatDau": "DATETIME(3)", "ThoiDiemKetThuc": "DATETIME(3)"},
    "TRUY_VAN_AI": {"ThoiDiem": "DATETIME(3)"},
    "GIU_CHO_MON": {"NgayTao": "DATETIME(3)", "ThoiDiemHetHan": "DATETIME(3)"},
    "CHI_TIET_GIU_CHO": {"SoLuongGiu": "DECIMAL(18,6)"},
    "LICH_GIO_BUSINESS_DATE": {"ThoiDiemBatDau": "DATETIME(3)"},
    "NGOAI_LE_THANH_TOAN": {
        "SoTien": "DECIMAL(18,2)",
        "SoTienHoan": "DECIMAL(18,2)",
        "NgayTao": "DATETIME(3)",
        "ThoiDiemXuLy": "DATETIME(3)",
    },
    "BO_NHO_DEM_SQL_AI": {"HetHanLuc": "DATETIME(3)"},
}

# Derived estimates: rounded instead of rejected when they have more than two decimals.
ROUNDED = {("GIA_BINH_QUAN_THANG", "DonGiaBinhQuan"), ("CHI_TIET_PHIEU_XUAT", "GiaVonUocTinh")}
INT_LIMIT = 2_147_483_647


def _scale(new: str) -> int | None:
    if new.startswith("DECIMAL(18,") and new.endswith(")"):
        return int(new.split(",")[1].rstrip(")"))
    return None


def _assert_no_precision_loss(bind, table: str, column: str, scale: int) -> None:
    lost = bind.execute(
        sa.text(
            f"SELECT COUNT(*) FROM `{table}` "
            f"WHERE `{column}` IS NOT NULL AND `{column}` <> ROUND(`{column}`, {scale})"
        )
    ).scalar_one()
    if lost:
        raise RuntimeError(
            f"{table}.{column}: {lost} row(s) hold more than {scale} decimals; "
            "round or correct them deliberately before narrowing the column."
        )


def _column_definition(bind, table: str, column: str, new_type: str, *, precise: bool) -> str:
    row = bind.execute(
        sa.text(
            "SELECT IS_NULLABLE, COLUMN_DEFAULT, EXTRA FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).one()
    null = "NULL" if row.IS_NULLABLE == "YES" else "NOT NULL"
    default = ""
    stamp = "CURRENT_TIMESTAMP(3)" if precise else "CURRENT_TIMESTAMP"
    if row.COLUMN_DEFAULT is not None:
        text = str(row.COLUMN_DEFAULT)
        if re.fullmatch(r"(now|current_timestamp)(\(\d*\))?", text, re.IGNORECASE):
            default = f" DEFAULT {stamp}"
        elif "DEFAULT_GENERATED" in (row.EXTRA or ""):
            raise RuntimeError(f"{table}.{column}: unsupported expression default {text!r}.")
        else:
            default = " DEFAULT '" + text.replace("'", "''") + "'"
    on_update = f" ON UPDATE {stamp}" if "on update" in (row.EXTRA or "").lower() else ""
    return f"MODIFY `{column}` {new_type} {null}{default}{on_update}"


def upgrade() -> None:
    bind = op.get_bind()
    for table, columns in COLUMNS.items():
        clauses = []
        for column, new in columns.items():
            scale = _scale(new)
            if scale == 2:
                if (table, column) in ROUNDED:
                    bind.execute(sa.text(f"UPDATE `{table}` SET `{column}` = ROUND(`{column}`, 2)"))
                else:
                    _assert_no_precision_loss(bind, table, column, 2)
            if new == "INT":
                top = bind.execute(
                    sa.text(f"SELECT MAX(ABS(`{column}`)) FROM `{table}`")
                ).scalar_one()
                if top is not None and top > INT_LIMIT:
                    raise RuntimeError(f"{table}.{column} holds a value that no longer fits INT.")
            clauses.append(_column_definition(bind, table, column, new, precise=True))
        op.execute(f"ALTER TABLE `{table}` " + ", ".join(clauses))


OLD_TYPES = {
    "DATETIME(3)": "DATETIME",
    "DECIMAL(18,6)": "DECIMAL(18,4)",
    "DECIMAL(18,2)": "DECIMAL(18,4)",
    "INT": "BIGINT",
}


def downgrade() -> None:
    bind = op.get_bind()
    for table, columns in COLUMNS.items():
        clauses = [
            _column_definition(bind, table, column, OLD_TYPES[new], precise=False)
            for column, new in columns.items()
        ]
        op.execute(f"ALTER TABLE `{table}` " + ", ".join(clauses))
