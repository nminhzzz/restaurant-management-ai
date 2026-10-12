"""Persist the Business Date used for each AI quota reservation.

Revision ID: 4e2d9f31a6bc
Revises: d2f8a7c4e901
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4e2d9f31a6bc"
down_revision: str | None = "d2f8a7c4e901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("TRUY_VAN_AI", sa.Column("BusinessDate", sa.Date(), nullable=True))
    # Before this column existed, the effective boundary was the project default (06:00).
    # Historical configuration snapshots were not retained, so use that documented default.
    op.execute(
        sa.text("UPDATE TRUY_VAN_AI SET BusinessDate = DATE(DATE_SUB(ThoiDiem, INTERVAL 6 HOUR))")
    )
    op.alter_column("TRUY_VAN_AI", "BusinessDate", existing_type=sa.Date(), nullable=False)
    op.create_index(
        "ix_TRUY_VAN_AI_BusinessDate_MaPhien",
        "TRUY_VAN_AI",
        ["BusinessDate", "MaPhien"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_TRUY_VAN_AI_BusinessDate_MaPhien", table_name="TRUY_VAN_AI")
    op.drop_column("TRUY_VAN_AI", "BusinessDate")
