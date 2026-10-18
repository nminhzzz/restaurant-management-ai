"""Technical state shared by all AI workers; no restaurant data is stored here."""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, BigInteger


class AiDailyUsage(Base):
    __tablename__ = "HAN_MUC_AI_NGAY"
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, primary_key=True)
    user_id: Mapped[int] = mapped_column("MaNguoiDung", BigInteger, primary_key=True, default=0)
    calls: Mapped[int] = mapped_column("SoLanGoi", Integer, nullable=False, server_default="0")
    __table_args__ = (CheckConstraint("SoLanGoi >= 0", name="nonnegative_calls"),)


class AiSqlCache(Base):
    __tablename__ = "BO_NHO_DEM_SQL_AI"
    key: Mapped[str] = mapped_column("KhoaCache", String(64), primary_key=True)
    sql_text: Mapped[str] = mapped_column("CauSQL", Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column("HetHanLuc", DateTime, nullable=False)
    __table_args__ = (Index("ix_BO_NHO_DEM_SQL_AI_HetHanLuc", "HetHanLuc"),)
