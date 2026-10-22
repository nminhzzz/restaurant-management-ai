"""SePay polling cursor so no transfer is skipped after downtime

Revision ID: b8e2a4c9d1f7
Revises: a6c9f2e8b7d1
Create Date: 2026-10-22 09:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b8e2a4c9d1f7"
down_revision: str | None = "a6c9f2e8b7d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("CAU_HINH_HE_THONG", sa.Column("MocDongBoSepay", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("CAU_HINH_HE_THONG", "MocDongBoSepay")
