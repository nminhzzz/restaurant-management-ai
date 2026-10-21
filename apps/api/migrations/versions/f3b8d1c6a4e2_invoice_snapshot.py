"""invoice content snapshot for unchanged reprints (FR-SALE-26)

Revision ID: f3b8d1c6a4e2
Revises: e1a4c7d9f2b6
Create Date: 2026-10-22 00:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f3b8d1c6a4e2"
down_revision: str | None = "e1a4c7d9f2b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("HOA_DON", sa.Column("NoiDungChup", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("HOA_DON", "NoiDungChup")
