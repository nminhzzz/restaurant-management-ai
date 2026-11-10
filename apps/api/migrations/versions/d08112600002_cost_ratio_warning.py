"""CAU_HINH_HE_THONG.TyLeGiaVonCanhBao (handoff 2026-11-08 A5, FR-SET-04, FR-CAT-29).

The share of the selling price, in percent, above which a dish's estimated ingredient cost is
flagged for the manager. Existing rows take the default of 40.

Revision ID: d08112600002
Revises: d08112600001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d08112600002"
down_revision: str | None = "d08112600001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "CAU_HINH_HE_THONG"
COLUMN = "TyLeGiaVonCanhBao"
CONSTRAINT = "ck_CAU_HINH_HE_THONG_cost_ratio_warning_range"


def upgrade() -> None:
    op.add_column(TABLE, sa.Column(COLUMN, sa.DECIMAL(5, 2), nullable=False, server_default="40"))
    op.create_check_constraint(op.f(CONSTRAINT), TABLE, f"{COLUMN} >= 1 AND {COLUMN} <= 100")


def downgrade() -> None:
    op.drop_constraint(op.f(CONSTRAINT), TABLE, type_="check")
    op.drop_column(TABLE, COLUMN)
