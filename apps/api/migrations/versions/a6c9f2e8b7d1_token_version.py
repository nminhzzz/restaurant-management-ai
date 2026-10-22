"""token version to revoke JWTs on password/role changes

Revision ID: a6c9f2e8b7d1
Revises: f3b8d1c6a4e2
Create Date: 2026-10-22 09:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a6c9f2e8b7d1"
down_revision: str | None = "f3b8d1c6a4e2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "NGUOI_DUNG",
        sa.Column("PhienBanToken", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    op.drop_column("NGUOI_DUNG", "PhienBanToken")
