"""scope ai quota per user

Revision ID: 0fee63547c48
Revises: 00450d24afd7
Create Date: 2026-10-18 15:59:27.686758
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0fee63547c48"
down_revision: str | None = "00450d24afd7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "HAN_MUC_AI_NGAY",
        sa.Column("MaNguoiDung", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.drop_constraint("pk_HAN_MUC_AI_NGAY", "HAN_MUC_AI_NGAY", type_="primary")
    op.create_primary_key("pk_HAN_MUC_AI_NGAY", "HAN_MUC_AI_NGAY", ["BusinessDate", "MaNguoiDung"])


def downgrade() -> None:
    op.drop_constraint("pk_HAN_MUC_AI_NGAY", "HAN_MUC_AI_NGAY", type_="primary")
    op.create_primary_key("pk_HAN_MUC_AI_NGAY", "HAN_MUC_AI_NGAY", ["BusinessDate"])
    op.drop_column("HAN_MUC_AI_NGAY", "MaNguoiDung")
