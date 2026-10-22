"""Seed a transaction-local counter from every existing invoice number.

Revision ID: c7f2d8a9e301
Revises: b8e2a4c9d1f7
"""

import sqlalchemy as sa
from alembic import op

revision = "c7f2d8a9e301"
down_revision = "b8e2a4c9d1f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    counter = op.create_table(
        "DEM_HOA_DON",
        sa.Column("BusinessDate", sa.Date(), primary_key=True),
        sa.Column("SoDaCap", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    invoices = sa.table(
        "HOA_DON", sa.column("BusinessDate", sa.Date()), sa.column("SoHoaDon", sa.String())
    )
    highest = (
        sa.select(
            invoices.c.BusinessDate,
            sa.func.max(sa.cast(sa.func.substring_index(invoices.c.SoHoaDon, "-", -1), sa.Integer)),
        )
        .where(invoices.c.SoHoaDon.like("HD-%"))
        .group_by(invoices.c.BusinessDate)
    )
    op.execute(counter.insert().from_select(["BusinessDate", "SoDaCap"], highest))


def downgrade() -> None:
    op.drop_table("DEM_HOA_DON")
