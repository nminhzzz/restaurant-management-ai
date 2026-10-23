"""AI module tables."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.modules.ai.runtime_models import AiDailyUsage, AiSqlCache  # noqa: F401
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
    role_id: Mapped[str | None] = mapped_column(
        "MaVaiTro",
        String(20),
        ForeignKey("VAI_TRO.MaVaiTro", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
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
    sql_text: Mapped[str | None] = mapped_column("CauSQLSinhRa", Text, nullable=True)
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Th\u00e0nh c\u00f4ng"
    )
    summary: Mapped[str | None] = mapped_column("KetQuaTomTat", Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column("ThoiGianPhanHoi", Integer, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    model_version: Mapped[str | None] = mapped_column("ModelPhienBan", Text, nullable=True)
    input_tokens: Mapped[int] = mapped_column(
        "TokenDauVao", Integer, nullable=False, default=0, server_default="0"
    )
    output_tokens: Mapped[int] = mapped_column(
        "TokenDauRa", Integer, nullable=False, default=0, server_default="0"
    )
    cost_usd: Mapped[Decimal | None] = mapped_column(
        "ChiPhiUSD", Numeric(18, 10).evaluates_none(), nullable=True, default=0, server_default="0"
    )
    call_count: Mapped[int] = mapped_column(
        "SoLanGoi", Integer, nullable=False, default=0, server_default="0"
    )
    usage_detail: Mapped[dict[str, Any] | None] = mapped_column(
        "ChiTietSuDung", JSON, nullable=True
    )
    payload: Mapped[dict[str, Any] | None] = mapped_column("PhanHoi", JSON, nullable=True)
    __table_args__ = (
        Index("ix_TRUY_VAN_AI_MaPhien_ThoiDiem", "MaPhien", "ThoiDiem"),
        CheckConstraint(
            "TokenDauVao >= 0 AND TokenDauRa >= 0 AND ChiPhiUSD >= 0 AND SoLanGoi >= 0",
            name="ck_ai_usage_nonnegative",
        ),
    )
