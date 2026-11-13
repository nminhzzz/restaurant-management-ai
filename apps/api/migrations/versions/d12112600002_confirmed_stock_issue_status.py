"""PHIEU_XUAT_KHO.TrangThai is 'Đã xác nhận' once the voucher posts stock (BA QA 2026-11-10 PH-05).

A manual issue writes its stock movements in the same transaction it is created in, so no
voucher is ever a draft. Rows written as 'Nháp' before this fix are relabelled.

Revision ID: d12112600002
Revises: d12112600001
"""

from collections.abc import Sequence

from alembic import op

revision: str = "d12112600002"
down_revision: str | None = "d12112600001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE PHIEU_XUAT_KHO SET TrangThai = 'Đã xác nhận' WHERE TrangThai = 'Nháp'")


def downgrade() -> None:
    # Irreversible by design: the old label was wrong, and stocktake vouchers were always
    # 'Đã xác nhận', so the rows that used to read 'Nháp' cannot be told apart.
    pass
