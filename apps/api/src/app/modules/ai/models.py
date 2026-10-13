"""AI module tables."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, BigInteger


class ChatSession(Base):
    __tablename__ = "PHIEN_CHAT_AI"
    id: Mapped[int] = mapped_column("MaPhien", BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        "MaNguoiDung",
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        "ThoiDiemBatDau", DateTime, server_default=func.now(), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        "MaVaiTro",
        String(20),
        ForeignKey("VAI_TRO.MaVaiTro", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column("ThoiDiemKetThuc", DateTime, nullable=True)


class AssistantQuery(Base):
    __tablename__ = "TRUY_VAN_AI"
    id: Mapped[int] = mapped_column("MaTruyVan", BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        "MaPhien",
        ForeignKey("PHIEN_CHAT_AI.MaPhien", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    scope: Mapped[str | None] = mapped_column("PhamViDuLieu", String(50), nullable=True)
    question: Mapped[str] = mapped_column("CauHoi", Text, nullable=False)
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
    sql_text: Mapped[str | None] = mapped_column("CauSQLSinhRa", Text, nullable=True)
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Th\u00e0nh c\u00f4ng"
    )
    summary: Mapped[str | None] = mapped_column("KetQuaTomTat", Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column("ThoiGianPhanHoi", Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    model_version: Mapped[str | None] = mapped_column("ModelPhienBan", String(100), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column("TokenDauVao", Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column("TokenDauRa", Integer, nullable=True)
    cost_usd: Mapped[Decimal | None] = mapped_column("ChiPhiUSD", DECIMAL(12, 6), nullable=True)
    call_count: Mapped[int | None] = mapped_column("SoLanGoi", Integer, nullable=True)
    __table_args__ = (
        CheckConstraint(
            "TokenDauVao IS NULL OR TokenDauVao >= 0", name="input_tokens_non_negative"
        ),
        CheckConstraint("TokenDauRa IS NULL OR TokenDauRa >= 0", name="output_tokens_non_negative"),
        CheckConstraint("ChiPhiUSD IS NULL OR ChiPhiUSD >= 0", name="cost_usd_non_negative"),
        CheckConstraint("SoLanGoi IS NULL OR SoLanGoi >= 0", name="call_count_non_negative"),
        Index("ix_TRUY_VAN_AI_MaPhien_ThoiDiem", "MaPhien", "ThoiDiem"),
        Index("ix_TRUY_VAN_AI_BusinessDate_MaPhien", "BusinessDate", "MaPhien"),
    )
