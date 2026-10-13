"""Sales alignment with the report: invoice snapshot, invoice numbers, line state name.

Revision ID: a9c4e7d2b6f1
Revises: e5b2c8d4f3a1

* HOA_DON.NoiDungHoaDon (JSON, NULL): the invoice as issued, so a reprint renders exactly the
  stored content (FR-SALE-26) instead of recomputing it from live data. Older invoices keep NULL
  and are rendered from their order lines once more.
* HOA_DON.SoHoaDon is filled for invoices that never had one (the column is UNIQUE since
  e5b2c8d4f3a1); new invoices get theirs from the application.
* PHIEN_CHAT_AI.MaVaiTro becomes NOT NULL: the report gives every chat session the role it was
  opened under (FR-AI-05, NFR-06); sessions still without one take their owner's role first.
* CHI_TIET_ORDER.TrangThai: the first state of a dish line is "Chờ làm" in the report
  (appendix D, FR-SALE-09); rows written before that read "Chờ".
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a9c4e7d2b6f1"
down_revision: str | None = "e5b2c8d4f3a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("HOA_DON", sa.Column("NoiDungHoaDon", sa.JSON(), nullable=True))
    op.execute(
        "UPDATE HOA_DON SET SoHoaDon = CONCAT('HD-', LPAD(DAY(BusinessDate), 2, '0'), "
        "LPAD(MONTH(BusinessDate), 2, '0'), LPAD(MOD(YEAR(BusinessDate), 100), 2, '0'), "
        "'-', LPAD(MaHoaDon, 6, '0')) WHERE SoHoaDon IS NULL"
    )
    op.execute("UPDATE CHI_TIET_ORDER SET TrangThai = 'Chờ làm' WHERE TrangThai = 'Chờ'")
    op.execute(
        "UPDATE PHIEN_CHAT_AI p JOIN NGUOI_DUNG u ON u.MaNguoiDung = p.MaNguoiDung "
        "SET p.MaVaiTro = u.MaVaiTro WHERE p.MaVaiTro IS NULL"
    )
    op.alter_column("PHIEN_CHAT_AI", "MaVaiTro", existing_type=sa.String(20), nullable=False)


def downgrade() -> None:
    op.alter_column("PHIEN_CHAT_AI", "MaVaiTro", existing_type=sa.String(20), nullable=True)
    op.execute("UPDATE CHI_TIET_ORDER SET TrangThai = 'Chờ' WHERE TrangThai = 'Chờ làm'")
    op.drop_column("HOA_DON", "NoiDungHoaDon")
