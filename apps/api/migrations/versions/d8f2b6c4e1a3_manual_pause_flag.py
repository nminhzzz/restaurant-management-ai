"""manual pause flag for dishes (FR-CAT-26/27)

Revision ID: d8f2b6c4e1a3
Revises: c7e1a9b4d2f0
Create Date: 2026-10-21 23:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8f2b6c4e1a3"
down_revision: str | None = "c7e1a9b4d2f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "MON_AN",
        sa.Column("TamDungThuCong", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    # HetNguyenLieu stays derived; the generated label must show a manual pause as its
    # own state, while an ingredient shortage keeps precedence (FR-CAT-27).
    op.execute(
        """
        ALTER TABLE MON_AN MODIFY COLUMN TrangThai VARCHAR(20) COLLATE utf8mb4_unicode_ci
        GENERATED ALWAYS AS (
            CASE
                WHEN ChuaCoCongThuc = 1 THEN 'Nháp'
                WHEN HetNguyenLieu = 1 THEN 'Hết nguyên liệu'
                WHEN TamDungThuCong = 1 THEN 'Tạm dừng phục vụ'
                ELSE 'Hoạt động'
            END
        ) STORED
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE MON_AN MODIFY COLUMN TrangThai VARCHAR(20) COLLATE utf8mb4_unicode_ci
        GENERATED ALWAYS AS (
            CASE
                WHEN ChuaCoCongThuc = 1 THEN 'Nháp'
                WHEN HetNguyenLieu = 1 THEN 'Hết nguyên liệu'
                ELSE 'Hoạt động'
            END
        ) STORED
        """
    )
    op.drop_column("MON_AN", "TamDungThuCong")
