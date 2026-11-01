"""Integrity rules of document 04 part G that the schema did not yet enforce.

* Quantities, prices and conversion factors are positive; a lot never holds negative stock.
* BR-LOT-02: a stocktake adjustment lot has no receipt line.
* A gateway reference (`MaGiaoDichCong`) identifies one payment transaction.
* The audit trail's foreign key to the user is an explicit RESTRICT.

Existing rows are checked first and the migration stops, naming the rule and the number of rows,
instead of letting MySQL fail with a generic constraint error. Lots whose received quantity was
never recorded (stocktake adjustment lots created before this rule) take what they still hold.
"""

import sqlalchemy as sa
from alembic import op

revision = "d01112600006"
down_revision = "d01112600005"
branch_labels = None
depends_on = None

CHECKS = [
    ("LICH_SU_GIA_MON", "price_positive", "GiaBan > 0"),
    ("CHI_TIET_CONG_THUC", "quantity_positive", "DinhLuong > 0"),
    ("CHI_TIET_ORDER", "quantity_positive", "SoLuong > 0"),
    ("CHI_TIET_PHIEU_NHAP", "quantity_positive", "SoLuong > 0"),
    ("CHI_TIET_PHIEU_NHAP", "conversion_factor_positive", "HeSoQuyDoi > 0"),
    ("CHI_TIET_PHIEU_XUAT", "quantity_positive", "SoLuong > 0"),
    ("LO_NGUYEN_LIEU", "received_quantity_positive", "SoLuongNhap > 0"),
    ("LO_NGUYEN_LIEU", "remaining_non_negative", "SoLuongConLai >= 0"),
    (
        "LO_NGUYEN_LIEU",
        "adjustment_has_no_receipt_line",
        "LoDieuChinhKiemKe = 0 OR MaChiTietNhap IS NULL",
    ),
]


def _name(table: str, name: str) -> str:
    return f"ck_{table}_{name}"


def _fail_on_violations(bind, table: str, rule: str, violating: str) -> None:
    count = bind.execute(sa.text(f"SELECT COUNT(*) FROM `{table}` WHERE {violating}")).scalar_one()
    if count:
        raise RuntimeError(
            f"{table}: {count} row(s) break '{rule}'; correct them before migrating."
        )


def upgrade() -> None:
    bind = op.get_bind()
    op.execute(
        "UPDATE LO_NGUYEN_LIEU SET SoLuongNhap = SoLuongConLai "
        "WHERE SoLuongNhap <= 0 AND SoLuongConLai > 0"
    )
    for table, _, expression in CHECKS:
        _fail_on_violations(bind, table, expression, f"NOT ({expression})")
    duplicated = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM (SELECT MaGiaoDichCong FROM GIAO_DICH_THANH_TOAN "
            "WHERE MaGiaoDichCong IS NOT NULL GROUP BY MaGiaoDichCong HAVING COUNT(*) > 1) d"
        )
    ).scalar_one()
    if duplicated:
        raise RuntimeError(
            f"GIAO_DICH_THANH_TOAN: {duplicated} gateway reference(s) are shared by several "
            "payments; resolve them before MaGiaoDichCong can be unique."
        )

    for table, name, expression in CHECKS:
        op.create_check_constraint(op.f(_name(table, name)), table, expression)
    op.create_unique_constraint(
        op.f("uq_GIAO_DICH_THANH_TOAN_MaGiaoDichCong"), "GIAO_DICH_THANH_TOAN", ["MaGiaoDichCong"]
    )
    op.drop_constraint(
        op.f("fk_NHAT_KY_HE_THONG_MaNguoiDung"), "NHAT_KY_HE_THONG", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_NHAT_KY_HE_THONG_MaNguoiDung"),
        "NHAT_KY_HE_THONG",
        "NGUOI_DUNG",
        ["MaNguoiDung"],
        ["MaNguoiDung"],
        ondelete="RESTRICT",
        onupdate="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint(
        op.f("fk_NHAT_KY_HE_THONG_MaNguoiDung"), "NHAT_KY_HE_THONG", type_="foreignkey"
    )
    op.create_foreign_key(
        op.f("fk_NHAT_KY_HE_THONG_MaNguoiDung"),
        "NHAT_KY_HE_THONG",
        "NGUOI_DUNG",
        ["MaNguoiDung"],
        ["MaNguoiDung"],
    )
    op.drop_constraint(
        op.f("uq_GIAO_DICH_THANH_TOAN_MaGiaoDichCong"), "GIAO_DICH_THANH_TOAN", type_="unique"
    )
    for table, name, _expression in reversed(CHECKS):
        op.drop_constraint(op.f(_name(table, name)), table, type_="check")
