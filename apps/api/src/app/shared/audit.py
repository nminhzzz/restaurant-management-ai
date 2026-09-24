"""Audit log for high-risk operations (FR-SET-08, FR-SET-09, NFR-07).

Append-only: the table is never updated or deleted by application code.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.shared.base import Base, BigInteger


class SystemAuditLog(Base):
    __tablename__ = "NHAT_KY_HE_THONG"

    id: Mapped[int] = mapped_column("MaNhatKy", BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        "MaNguoiDung", BigInteger, ForeignKey("NGUOI_DUNG.MaNguoiDung"), nullable=False
    )
    occurred_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    action: Mapped[str] = mapped_column("LoaiThaoTac", String(50), nullable=False)
    target_entity: Mapped[str] = mapped_column("DoiTuong", String(50), nullable=False)
    target_id: Mapped[str] = mapped_column("MaDoiTuong", String(50), nullable=False)
    before: Mapped[dict[str, Any] | None] = mapped_column("DuLieuTruoc", JSON, nullable=True)
    after: Mapped[dict[str, Any] | None] = mapped_column("DuLieuSau", JSON, nullable=True)
    reason: Mapped[str | None] = mapped_column("LyDo", String(255), nullable=True)

    __table_args__ = (Index("ix_NHAT_KY_HE_THONG_ThoiDiem", "ThoiDiem"),)


def record(
    session: Session,
    *,
    user_id: int,
    action: str,
    target_entity: str,
    target_id: str | int,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    reason: str | None = None,
) -> SystemAuditLog:
    entry = SystemAuditLog(
        user_id=user_id,
        action=action,
        target_entity=target_entity,
        target_id=str(target_id),
        before=before,
        after=after,
        reason=reason,
    )
    session.add(entry)
    return entry
