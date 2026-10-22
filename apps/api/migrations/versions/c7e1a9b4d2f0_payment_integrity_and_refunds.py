"""payment integrity: invoice numbers, bank reference uniqueness, refund details

Revision ID: c7e1a9b4d2f0
Revises: a1b2c3d4e5f6
Create Date: 2026-10-21 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7e1a9b4d2f0"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "NGOAI_LE_THANH_TOAN", sa.Column("MaThamChieuHoan", sa.String(100), nullable=True)
    )
    op.add_column("NGOAI_LE_THANH_TOAN", sa.Column("SoTienHoan", sa.DECIMAL(18, 4), nullable=True))

    # FR-SALE-21 / report Bảng 30: every invoice gets its own number, sequential
    # inside a business date. Existing rows were issued without one, so backfill
    # them in id order before the unique index goes on.
    op.execute(
        """
        UPDATE HOA_DON h
        JOIN (
            SELECT MaHoaDon,
                   CONCAT(
                       'HD-', DATE_FORMAT(BusinessDate, '%Y%m%d'), '-',
                       LPAD(ROW_NUMBER() OVER (
                           PARTITION BY BusinessDate ORDER BY MaHoaDon
                       ), 4, '0')
                   ) AS SoMoi
            FROM HOA_DON
        ) numbered ON numbered.MaHoaDon = h.MaHoaDon
        SET h.SoHoaDon = numbered.SoMoi
        WHERE h.SoHoaDon IS NULL
        """
    )

    # Two webhook deliveries of one transfer must not both be usable. Older rows may
    # repeat a manually typed reference; keep the data by suffixing the transaction id.
    op.execute(
        """
        UPDATE GIAO_DICH_THANH_TOAN t
        JOIN (
            SELECT MaGiaoDichTT,
                   ROW_NUMBER() OVER (
                       PARTITION BY MaGiaoDichNganHang ORDER BY MaGiaoDichTT
                   ) AS LanXuatHien
            FROM GIAO_DICH_THANH_TOAN
            WHERE MaGiaoDichNganHang IS NOT NULL
        ) dup ON dup.MaGiaoDichTT = t.MaGiaoDichTT
        SET t.MaGiaoDichNganHang = CONCAT(t.MaGiaoDichNganHang, '#', t.MaGiaoDichTT)
        WHERE dup.LanXuatHien > 1
        """
    )

    op.create_index(
        "uq_GIAO_DICH_THANH_TOAN_MaGiaoDichNganHang",
        "GIAO_DICH_THANH_TOAN",
        ["MaGiaoDichNganHang"],
        unique=True,
    )
    op.create_index("uq_HOA_DON_SoHoaDon", "HOA_DON", ["SoHoaDon"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_HOA_DON_SoHoaDon", table_name="HOA_DON")
    op.drop_index("uq_GIAO_DICH_THANH_TOAN_MaGiaoDichNganHang", table_name="GIAO_DICH_THANH_TOAN")
    op.drop_column("NGOAI_LE_THANH_TOAN", "SoTienHoan")
    op.drop_column("NGOAI_LE_THANH_TOAN", "MaThamChieuHoan")
