"""add dish image column

Revision ID: cd3a65232bee
Revises: 913679962ce8
Create Date: 2026-09-25 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cd3a65232bee"
down_revision: str | None = "913679962ce8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("MON_AN", sa.Column("HinhAnh", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("MON_AN", "HinhAnh")
