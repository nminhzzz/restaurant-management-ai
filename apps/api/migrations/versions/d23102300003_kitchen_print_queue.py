"""Durable kitchen printer delivery queue.

Revision ID: d23102300003
Revises: d23102300002
"""

import sqlalchemy as sa
from alembic import op

revision = "d23102300003"
down_revision = "d23102300002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "PHIEU_BEP", sa.Column("SoLanThuTrongDot", sa.Integer(), nullable=False, server_default="0")
    )
    op.add_column("PHIEU_BEP", sa.Column("LanThuTiepTheo", sa.DateTime(), nullable=True))
    op.add_column("PHIEU_BEP", sa.Column("MaKhoaIn", sa.String(36), nullable=True))
    op.add_column("PHIEU_BEP", sa.Column("HanKhoaIn", sa.DateTime(), nullable=True))
    op.add_column("PHIEU_BEP", sa.Column("LoiIn", sa.String(500), nullable=True))
    op.add_column("PHIEU_BEP", sa.Column("ThoiDiemIn", sa.DateTime(), nullable=True))
    op.create_index("ix_PHIEU_BEP_HangDoi", "PHIEU_BEP", ["TrangThaiIn", "LanThuTiepTheo"])
    # Browser dialog state in legacy rows cannot establish physical delivery.
    # Never automatically print historical orders when enabling the new worker.
    tickets = sa.table(
        "PHIEU_BEP", sa.column("TrangThaiIn"), sa.column("TrangThai"), sa.column("LoiIn")
    )
    op.execute(
        tickets.update().values(
            TrangThaiIn="Chưa rõ kết quả",
            TrangThai="Chưa rõ kết quả",
            LoiIn="Phiếu cũ trước hàng đợi máy chủ; kiểm tra thực tế trước khi in lại.",
        )
    )


def downgrade() -> None:
    op.drop_index("ix_PHIEU_BEP_HangDoi", table_name="PHIEU_BEP")
    for name in (
        "ThoiDiemIn",
        "LoiIn",
        "HanKhoaIn",
        "MaKhoaIn",
        "LanThuTiepTheo",
        "SoLanThuTrongDot",
    ):
        op.drop_column("PHIEU_BEP", name)
