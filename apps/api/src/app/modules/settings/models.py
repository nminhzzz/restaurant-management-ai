"""Settings module tables: VAI_TRO, NGUOI_DUNG, CAU_HINH_HE_THONG."""

from datetime import datetime, time

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Time, func
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class RoleTable(Base):
    __tablename__ = "VAI_TRO"

    id: Mapped[int] = mapped_column("MaVaiTro", String(20), primary_key=True)
    name: Mapped[str] = mapped_column("TenVaiTro", String(50), nullable=False)
    description: Mapped[str | None] = mapped_column("MoTa", String(255), nullable=True)


class User(Base):
    __tablename__ = "NGUOI_DUNG"

    id: Mapped[int] = mapped_column("MaNguoiDung", BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column("TenDangNhap", String(50), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column("MatKhauHash", String(255), nullable=False)
    full_name: Mapped[str] = mapped_column("HoTen", String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column("SoDienThoai", String(20), nullable=True)
    role_id: Mapped[str] = mapped_column(
        "MaVaiTro",
        String(20),
        ForeignKey("VAI_TRO.MaVaiTro", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Hoạt động"
    )
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )

    __table_args__ = (Index("ix_NGUOI_DUNG_MaVaiTro", "MaVaiTro"),)


class SystemConfig(Base):
    __tablename__ = "CAU_HINH_HE_THONG"

    id: Mapped[int] = mapped_column("MaCauHinh", BigInteger, primary_key=True, autoincrement=True)
    restaurant_name: Mapped[str] = mapped_column(
        "TenNhaHang", String(100), nullable=False, default="Nhà hàng"
    )
    address: Mapped[str | None] = mapped_column("DiaChi", String(255), nullable=True)
    invoice_template: Mapped[str | None] = mapped_column("MauHoaDon", String(50), nullable=True)
    default_stock_threshold: Mapped[int] = mapped_column(
        "NguongTonMacDinh", Integer, nullable=False, default=10
    )
    business_day_start: Mapped[time] = mapped_column(
        "GioBatDauBusinessDate", Time, nullable=False, default=time(hour=6)
    )
