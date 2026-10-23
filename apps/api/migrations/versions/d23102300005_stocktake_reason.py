"""Record why a stocktake count differs from the system quantity (FR-INV-08).

Revision ID: d23102300005
Revises: d23102300004
"""

import sqlalchemy as sa
from alembic import op

revision = "d23102300005"
down_revision = "d23102300004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "CHI_TIET_KIEM_KE",
        sa.Column("LyDoChenhLech", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("CHI_TIET_KIEM_KE", "LyDoChenhLech")
