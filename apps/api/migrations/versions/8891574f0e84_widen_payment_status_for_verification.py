"""widen payment status for verification

Revision ID: 8891574f0e84
Revises: eacd6036a5ab
Create Date: 2026-10-18 16:17:33.696589
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "8891574f0e84"
down_revision: str | None = "eacd6036a5ab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "GIAO_DICH_THANH_TOAN",
        "TrangThai",
        existing_type=sa.String(20),
        type_=sa.String(40),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "GIAO_DICH_THANH_TOAN",
        "TrangThai",
        existing_type=sa.String(40),
        type_=sa.String(20),
        existing_nullable=False,
    )
