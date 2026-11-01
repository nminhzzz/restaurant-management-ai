"""Business status values follow the specification (FR-INV-02/08/09, FR-SALE-19..23, FR-SALE-09).

* PHIEU_NHAP_KHO: "Nháp" -> "Hiệu lực" (a receipt is in force until cancelled).
* PHIEU_KIEM_KE: "Nháp" -> "Đang kiểm kê", "Đã chốt" -> "Đã xác nhận".
* "Chờ đối soát" / "Tranh chấp" were never business states: an order or payment in either one
  waits for the same manager decision as "Chờ xác minh thanh toán" (FR-SALE-19..23), so rows
  are folded into it.
* CHI_TIET_ORDER: "Chờ" -> "Chờ làm", the label the specification uses for the first line state.

Downgrade restores the old values; rows folded into "Chờ xác minh thanh toán" cannot be told
apart from genuine ones and stay there.
"""

from alembic import op

revision = "d01112600004"
down_revision = "d01112600003"
branch_labels = None
depends_on = None


def _swap(table: str, column: str, old: str, new: str) -> None:
    op.execute(f"UPDATE `{table}` SET {column} = '{new}' WHERE {column} = '{old}'")


def upgrade() -> None:
    _swap("PHIEU_NHAP_KHO", "TrangThai", "Nháp", "Hiệu lực")
    _swap("PHIEU_KIEM_KE", "TrangThai", "Nháp", "Đang kiểm kê")
    _swap("PHIEU_KIEM_KE", "TrangThai", "Đã chốt", "Đã xác nhận")
    for table in ("ORDER", "GIAO_DICH_THANH_TOAN"):
        for legacy in ("Chờ đối soát", "Tranh chấp"):
            _swap(table, "TrangThai", legacy, "Chờ xác minh thanh toán")
    _swap("CHI_TIET_ORDER", "TrangThai", "Chờ", "Chờ làm")


def downgrade() -> None:
    _swap("CHI_TIET_ORDER", "TrangThai", "Chờ làm", "Chờ")
    _swap("PHIEU_KIEM_KE", "TrangThai", "Đã xác nhận", "Đã chốt")
    _swap("PHIEU_KIEM_KE", "TrangThai", "Đang kiểm kê", "Nháp")
    _swap("PHIEU_NHAP_KHO", "TrangThai", "Hiệu lực", "Nháp")
