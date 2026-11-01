"""Unknown costs are NULL, not 0 (QD-02).

A stocktake surplus lot with no price basis and a write-off line that could not be priced used to
carry 0, which made "unknown" indistinguishable from "free" and let totals look complete.
Existing zero values on those two kinds of row meant exactly "unknown" (the month close treated
0 as unpriced), so they are converted. Purchase lots keep their price: a genuine free sample is
a purchase receipt line, not an adjustment lot.

Downgrade restores 0 for every NULL, which loses the unknown/zero distinction again.
"""

import sqlalchemy as sa
from alembic import op

revision = "d01112600003"
down_revision = "d01112600002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "LO_NGUYEN_LIEU",
        "DonGia",
        existing_type=sa.DECIMAL(precision=18, scale=4),
        nullable=True,
    )
    op.alter_column(
        "CHI_TIET_PHIEU_XUAT",
        "GiaVonUocTinh",
        existing_type=sa.DECIMAL(precision=18, scale=4),
        nullable=True,
    )
    op.execute("UPDATE LO_NGUYEN_LIEU SET DonGia = NULL WHERE LoDieuChinhKiemKe = 1 AND DonGia = 0")
    op.execute("UPDATE CHI_TIET_PHIEU_XUAT SET GiaVonUocTinh = NULL WHERE GiaVonUocTinh = 0")


def downgrade() -> None:
    op.execute("UPDATE CHI_TIET_PHIEU_XUAT SET GiaVonUocTinh = 0 WHERE GiaVonUocTinh IS NULL")
    op.execute("UPDATE LO_NGUYEN_LIEU SET DonGia = 0 WHERE DonGia IS NULL")
    op.alter_column(
        "CHI_TIET_PHIEU_XUAT",
        "GiaVonUocTinh",
        existing_type=sa.DECIMAL(precision=18, scale=4),
        nullable=False,
    )
    op.alter_column(
        "LO_NGUYEN_LIEU",
        "DonGia",
        existing_type=sa.DECIMAL(precision=18, scale=4),
        nullable=False,
    )
