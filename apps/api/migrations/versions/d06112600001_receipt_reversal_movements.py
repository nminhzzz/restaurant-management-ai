"""Allow a cancelled receipt to record its stock reversal.

The initial schema only accepted 'Hoàn kho' for order lines, so MySQL rejected the
reversal written by FR-INV-02 although the model already allowed it.

Revision ID: d06112600001
Revises: d01112600007
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d06112600001"
down_revision: str | None = "d01112600007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "GIAO_DICH_KHO"
CONSTRAINT = "ck_GIAO_DICH_KHO_movement_source_matches_kind"
OTHER_KINDS = (
    "(LoaiGiaoDich = 'Nhập' AND MaChiTietNhap IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Xuất thủ công' AND MaChiTietXuat IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Điều chỉnh kiểm kê' AND MaChiTietKiemKe IS NOT NULL)"
)
UPGRADED = (
    f"({OTHER_KINDS} OR "
    "(LoaiGiaoDich = 'Trừ tự động' AND MaChiTietOrder IS NOT NULL) OR "
    "(LoaiGiaoDich = 'Hoàn kho' AND (MaChiTietOrder IS NOT NULL "
    "OR MaChiTietNhap IS NOT NULL OR MaChiTietKiemKe IS NOT NULL)))"
)
ORIGINAL = (
    f"({OTHER_KINDS} OR "
    "(LoaiGiaoDich IN ('Trừ tự động','Hoàn kho') AND MaChiTietOrder IS NOT NULL))"
)


def _replace(condition: str) -> None:
    op.drop_constraint(op.f(CONSTRAINT), TABLE, type_="check")
    op.create_check_constraint(op.f(CONSTRAINT), TABLE, condition)


def upgrade() -> None:
    _replace(UPGRADED)


def downgrade() -> None:
    _replace(ORIGINAL)
