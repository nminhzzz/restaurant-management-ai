"""Persist effective-dated Business Date cutoff boundaries.

Revision ID: d23102300001
Revises: c7f2d8a9e301
"""

from datetime import date, datetime, time

import sqlalchemy as sa
from alembic import op

revision = "d23102300001"
down_revision = "c7f2d8a9e301"
branch_labels = None
depends_on = None


def upgrade() -> None:
    schedule = op.create_table(
        "LICH_GIO_BUSINESS_DATE",
        sa.Column("NgayHieuLuc", sa.Date(), primary_key=True),
        sa.Column("GioBatDau", sa.Time(), nullable=False),
        sa.Column("ThoiDiemBatDau", sa.DateTime(), nullable=False),
    )
    config = sa.table("CAU_HINH_HE_THONG", sa.column("GioBatDauBusinessDate", sa.Time()))
    cutoff = op.get_bind().execute(sa.select(config.c.GioBatDauBusinessDate).limit(1)).scalar()
    initial = cutoff if isinstance(cutoff, time) else time(6)
    # MySQL DATE starts at year 1000. All supported operational data is later.
    op.bulk_insert(
        schedule,
        [
            {
                "NgayHieuLuc": date(1000, 1, 1),
                "GioBatDau": initial,
                "ThoiDiemBatDau": datetime.combine(date(1000, 1, 1), initial),
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("LICH_GIO_BUSINESS_DATE")
