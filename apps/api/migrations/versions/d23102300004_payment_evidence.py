"""Store the payment evidence attached to a verification request (FR-SALE-19).

Revision ID: d23102300004
Revises: d23102300003
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

revision = "d23102300004"
down_revision = "d23102300003"
branch_labels = None
depends_on = None


def _large_text():
    return mysql.LONGTEXT() if op.get_bind().dialect.name == "mysql" else sa.Text()


def upgrade() -> None:
    op.alter_column(
        "GIAO_DICH_THANH_TOAN",
        "AnhChungTu",
        existing_type=sa.String(500),
        type_=_large_text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "GIAO_DICH_THANH_TOAN",
        "AnhChungTu",
        existing_type=_large_text(),
        type_=sa.String(500),
        existing_nullable=True,
    )
