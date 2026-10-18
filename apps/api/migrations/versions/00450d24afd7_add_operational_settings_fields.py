"""add operational settings fields

Revision ID: 00450d24afd7
Revises: e31f52a6c901
Create Date: 2026-10-18 15:53:18.410716
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "00450d24afd7"
down_revision: str | None = "e31f52a6c901"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "CAU_HINH_HE_THONG",
        sa.Column("SoNgayCanhBaoHetHan", sa.Integer(), nullable=False, server_default="3"),
    )
    op.add_column(
        "CAU_HINH_HE_THONG",
        sa.Column("ThoiGianGiuChoPhut", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column(
        "CAU_HINH_HE_THONG",
        sa.Column("SoCauHoiAIMoiNgay", sa.Integer(), nullable=False, server_default="50"),
    )
    op.create_check_constraint(
        "ck_CAU_HINH_HE_THONG_expiry_warning_nonnegative",
        "CAU_HINH_HE_THONG",
        "SoNgayCanhBaoHetHan >= 0",
    )
    op.create_check_constraint(
        "ck_CAU_HINH_HE_THONG_hold_minutes_positive",
        "CAU_HINH_HE_THONG",
        "ThoiGianGiuChoPhut > 0",
    )
    op.create_check_constraint(
        "ck_CAU_HINH_HE_THONG_ai_quota_positive",
        "CAU_HINH_HE_THONG",
        "SoCauHoiAIMoiNgay > 0",
    )


def downgrade() -> None:
    op.drop_constraint("ck_CAU_HINH_HE_THONG_ai_quota_positive", "CAU_HINH_HE_THONG", type_="check")
    op.drop_constraint(
        "ck_CAU_HINH_HE_THONG_hold_minutes_positive", "CAU_HINH_HE_THONG", type_="check"
    )
    op.drop_constraint(
        "ck_CAU_HINH_HE_THONG_expiry_warning_nonnegative", "CAU_HINH_HE_THONG", type_="check"
    )
    op.drop_column("CAU_HINH_HE_THONG", "SoCauHoiAIMoiNgay")
    op.drop_column("CAU_HINH_HE_THONG", "ThoiGianGiuChoPhut")
    op.drop_column("CAU_HINH_HE_THONG", "SoNgayCanhBaoHetHan")
