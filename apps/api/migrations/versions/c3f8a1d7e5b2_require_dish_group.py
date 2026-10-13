"""MON_AN.MaNhomMon becomes NOT NULL: every dish belongs to exactly one group.

Revision ID: c3f8a1d7e5b2
Revises: a9c4e7d2b6f1

The report (appendix D, MON_AN) gives each dish "đúng một nhóm" and keeps the foreign key to
NHOM_MON at ON DELETE/ON UPDATE RESTRICT, which it already is. Dishes still without a group
(rows written before the application insisted on one, soft-deleted ones included) are moved to
a group called "Chưa phân nhóm", created here only when it is needed and no live group of that
name exists yet.

The downgrade only makes the column nullable again; the adopted dishes and the group stay,
since nothing records which dishes were orphans.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3f8a1d7e5b2"
down_revision: str | None = "a9c4e7d2b6f1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_GROUP = "Chưa phân nhóm"


def upgrade() -> None:
    # The derived table keeps the INSERT ... SELECT to a single row that the WHERE can filter out
    # (a bare aggregate would return one row even when nothing qualifies).
    op.execute(
        "INSERT INTO NHOM_MON (TenNhomMon, ThuTuHienThi, DaXoa) "
        f"SELECT '{DEFAULT_GROUP}', next_slot.slot, 0 "
        "FROM (SELECT COALESCE(MAX(ThuTuHienThi), 0) + 1 AS slot FROM NHOM_MON) AS next_slot "
        "WHERE EXISTS (SELECT 1 FROM MON_AN WHERE MaNhomMon IS NULL) "
        f"AND NOT EXISTS (SELECT 1 FROM NHOM_MON WHERE TenNhomMon = '{DEFAULT_GROUP}' "
        "AND DaXoa = 0)"
    )
    op.execute(
        "UPDATE MON_AN SET MaNhomMon = ("
        f"SELECT MIN(MaNhomMon) FROM NHOM_MON WHERE TenNhomMon = '{DEFAULT_GROUP}' AND DaXoa = 0"
        ") WHERE MaNhomMon IS NULL"
    )
    op.alter_column("MON_AN", "MaNhomMon", existing_type=sa.BigInteger(), nullable=False)


def downgrade() -> None:
    op.alter_column("MON_AN", "MaNhomMon", existing_type=sa.BigInteger(), nullable=True)
