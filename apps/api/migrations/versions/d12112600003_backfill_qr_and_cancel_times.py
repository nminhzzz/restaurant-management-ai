"""Fill ThoiDiemTaoQR and the close time of cancelled orders (BA QA 2026-11-10 TC-SALE-74, PH-09).

Before this fix a QR payment never wrote GIAO_DICH_THANH_TOAN.ThoiDiemTaoQR (the API echoed
NgayTao instead), and cancelling an order left ORDER.ThoiDiemDong NULL. The QR is created in
the same statement as its row, and cancelling is the order's last update, so both values are
recoverable from columns already stored.

Revision ID: d12112600003
Revises: d12112600002
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d12112600003"
down_revision: str | None = "d12112600002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE GIAO_DICH_THANH_TOAN SET ThoiDiemTaoQR = NgayTao "
        "WHERE PhuongThuc = 'QR' AND ThoiDiemTaoQR IS NULL"
    )
    op.execute(
        "UPDATE `ORDER` SET ThoiDiemDong = NgayCapNhat "
        "WHERE TrangThai = 'Đã hủy' AND ThoiDiemDong IS NULL AND NgayCapNhat IS NOT NULL"
    )


def downgrade() -> None:
    # Data repair only: the filled values are what the fixed code writes, so there is
    # nothing to undo.
    pass
