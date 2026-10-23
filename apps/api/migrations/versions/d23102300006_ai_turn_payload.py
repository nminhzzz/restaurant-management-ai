"""Persist the full answer so reopening history keeps its table and chart (FR-AI-07/08).

Revision ID: d23102300006
Revises: d23102300005
"""

import sqlalchemy as sa
from alembic import op

revision = "d23102300006"
down_revision = "d23102300005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("TRUY_VAN_AI", sa.Column("PhanHoi", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("TRUY_VAN_AI", "PhanHoi")
