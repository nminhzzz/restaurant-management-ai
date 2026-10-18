"""make audit and ai logs append-only

Revision ID: f8db86d6d0a4
Revises: 93c8f84d573a
Create Date: 2026-10-18 17:56:16.583076
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f8db86d6d0a4"
down_revision: str | None = "93c8f84d573a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


TABLES = ("NHAT_KY_HE_THONG", "TRUY_VAN_AI")


def upgrade() -> None:
    for table in TABLES:
        for operation in ("UPDATE", "DELETE"):
            trigger = f"trg_{table}_no_{operation.lower()}"
            op.execute(
                f"CREATE TRIGGER {trigger} BEFORE {operation} ON {table} "
                f"FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = "
                f"'{table} is append-only'"
            )


def downgrade() -> None:
    for table in TABLES:
        for operation in ("UPDATE", "DELETE"):
            op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_no_{operation.lower()}")
