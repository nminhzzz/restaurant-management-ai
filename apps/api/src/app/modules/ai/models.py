"""AI module tables."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class ChatSession(Base):
    __tablename__ = "PHIEN_CHAT_AI"
    id: Mapped[int] = mapped_column("MaPhien", BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        "MaNguoiDung",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )


class AssistantQuery(Base):
    __tablename__ = "TRUY_VAN_AI"
    id: Mapped[int] = mapped_column("MaTruyVan", BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        "MaPhien",
        BigInteger,
        ForeignKey("PHIEN_CHAT_AI.MaPhien", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    scope: Mapped[str | None] = mapped_column("PhamViDuLieu", String(50), nullable=True)
    question: Mapped[str] = mapped_column("CauHoi", Text, nullable=False)
    sql_text: Mapped[str | None] = mapped_column("CauSQLSinhRa", Text, nullable=True)
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Th\u00e0nh c\u00f4ng"
    )
    summary: Mapped[str | None] = mapped_column("KetQuaTomTat", Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column("ThoiGianPhanHoi", Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    __table_args__ = (Index("ix_TRUY_VAN_AI_MaPhien_ThoiDiem", "MaPhien", "ThoiDiem"),)
