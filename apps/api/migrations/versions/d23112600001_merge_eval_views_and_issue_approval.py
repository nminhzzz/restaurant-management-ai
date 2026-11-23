"""Join the two heads that both follow d13112600001.

d14112600001 (precomputed metric-group views for the assistant, eval v2) and d19112600001
(write-off approval, supervisor review 2026-11-19) were built on separate branches. They
touch different objects, so this revision only joins the history; it changes no schema.

Revision ID: d23112600001
Revises: d14112600001, d19112600001
"""

from collections.abc import Sequence

revision: str = "d23112600001"
down_revision: str | Sequence[str] | None = ("d14112600001", "d19112600001")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
