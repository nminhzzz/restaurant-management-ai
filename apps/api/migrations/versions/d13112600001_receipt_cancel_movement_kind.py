"""Record a cancelled receipt line as 'Hủy nhập' instead of 'Hoàn kho' (PH-04).

Document 04 F.26 ties 'Hoàn kho' to an order line only. Cancelling a receipt now has its
own kind, sourced by MaChiTietNhap, so reports and the assistant never mix the two.

Revision ID: d13112600001
Revises: d12112600003
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d13112600001"
down_revision: str | None = "d12112600003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "GIAO_DICH_KHO"
CONSTRAINT = "ck_GIAO_DICH_KHO_movement_source_matches_kind"
OTHER_KINDS = (
    "(LoaiGiaoDich = 'Nhập' AND MaChiTietNhap IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Trừ tự động' AND MaChiTietOrder IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Xuất thủ công' AND MaChiTietXuat IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Điều chỉnh kiểm kê' AND MaChiTietKiemKe IS NOT NULL)"
)
UPGRADED = (
    f"({OTHER_KINDS} OR "
    "(LoaiGiaoDich = 'Hủy nhập' AND MaChiTietNhap IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Hoàn kho' AND MaChiTietOrder IS NOT NULL))"
)
PREVIOUS = (
    f"({OTHER_KINDS} OR "
    "(LoaiGiaoDich = 'Hoàn kho' AND (MaChiTietOrder IS NOT NULL "
    "OR MaChiTietNhap IS NOT NULL OR MaChiTietKiemKe IS NOT NULL)))"
)


def _replace(condition: str) -> None:
    op.drop_constraint(op.f(CONSTRAINT), TABLE, type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), TABLE, condition)


def upgrade() -> None:
    # Widen first so the relabelled rows are valid at every step, then tighten.
    _replace(f"({PREVIOUS[1:-1]} OR (LoaiGiaoDich = 'Hủy nhập' AND MaChiTietNhap IS NOT NULL))")
    op.execute(
        f"UPDATE {TABLE} SET LoaiGiaoDich = 'Hủy nhập' "
        "WHERE LoaiGiaoDich = 'Hoàn kho' AND MaChiTietOrder IS NULL AND MaChiTietNhap IS NOT NULL"
    )
    _replace(UPGRADED)


def downgrade() -> None:
    _replace(f"({PREVIOUS[1:-1]} OR (LoaiGiaoDich = 'Hủy nhập' AND MaChiTietNhap IS NOT NULL))")
    op.execute(f"UPDATE {TABLE} SET LoaiGiaoDich = 'Hoàn kho' WHERE LoaiGiaoDich = 'Hủy nhập'")
    _replace(PREVIOUS)
