"""add order request ids

Revision ID: a1b2c3d4e5f6
Revises: 4f7a1c2d9e10
Create Date: 2026-10-21 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "4f7a1c2d9e10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ORDER", sa.Column("MaYeuCauGui", sa.String(36), nullable=True))
    op.create_unique_constraint("uq_ORDER_MaYeuCauGui", "ORDER", ["MaYeuCauGui"])
    op.add_column("CHI_TIET_ORDER", sa.Column("MaYeuCauDong", sa.String(36), nullable=True))
    op.create_unique_constraint(
        "uq_CHI_TIET_ORDER_MaYeuCauDong", "CHI_TIET_ORDER", ["MaYeuCauDong"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_CHI_TIET_ORDER_MaYeuCauDong", "CHI_TIET_ORDER", type_="unique")
    op.drop_column("CHI_TIET_ORDER", "MaYeuCauDong")
    op.drop_constraint("uq_ORDER_MaYeuCauGui", "ORDER", type_="unique")
    op.drop_column("ORDER", "MaYeuCauGui")
