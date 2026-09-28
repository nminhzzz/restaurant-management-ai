"""Sales module tables."""

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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import (  # PaymentTransaction defaults match enums.PaymentStatus values
    Base,
    BigInteger,
)


class DemOrder(Base):
    __tablename__ = "DEM_ORDER"
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, primary_key=True)
    count: Mapped[int] = mapped_column("SoDaCap", Integer, nullable=False, default=1)


class Order(Base):
    __tablename__ = "ORDER"
    id: Mapped[int] = mapped_column("MaOrder", BigInteger, primary_key=True, autoincrement=True)
    display_code: Mapped[str | None] = mapped_column(
        "MaOrderHienThi", String(30), nullable=True, unique=True
    )
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
    table_id: Mapped[int | None] = mapped_column(
        "MaBan",
        ForeignKey("BAN.MaBan", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    order_type: Mapped[str] = mapped_column(
        "LoaiDon", String(20), nullable=False, default="T\u1ea1i ch\u1ed7"
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(30), nullable=False, default="\u0110ang m\u1edf"
    )
    cancel_reason: Mapped[str | None] = mapped_column("LyDoHuy", String(500), nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column("NgayCapNhat", DateTime, nullable=True)
    total: Mapped[Decimal] = mapped_column(
        "TongTien", DECIMAL(18, 4), nullable=False, default=Decimal("0")
    )
    closed_at: Mapped[datetime | None] = mapped_column("ThoiDiemDong", DateTime, nullable=True)
    __table_args__ = (
        CheckConstraint(
            "(LoaiDon = 'T\u1ea1i ch\u1ed7' AND MaBan IS NOT NULL) "
            "OR (LoaiDon = 'Mang v\u1ec1' AND MaBan IS NULL)",
            name="dine_in_needs_a_table",
        ),
        Index("ix_ORDER_BusinessDate_MaBan", "BusinessDate", "MaBan"),
    )


class OrderLine(Base):
    __tablename__ = "CHI_TIET_ORDER"
    id: Mapped[int] = mapped_column(
        "MaChiTietOrder", BigInteger, primary_key=True, autoincrement=True
    )
    order_id: Mapped[int] = mapped_column(
        "MaOrder",
        ForeignKey("ORDER.MaOrder", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    dish_id: Mapped[int] = mapped_column(
        "MaMon",
        ForeignKey("MON_AN.MaMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    price_version_id: Mapped[int | None] = mapped_column(
        "MaPhienBanGia",
        ForeignKey("LICH_SU_GIA_MON.MaPhienBanGia", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    recipe_id: Mapped[int | None] = mapped_column(
        "MaCongThuc",
        ForeignKey("CONG_THUC.MaCongThuc", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column("GhiChu", String(500), nullable=True)
    quantity: Mapped[int] = mapped_column("SoLuong", nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(
        "DonGia", DECIMAL(18, 4), nullable=False, default=Decimal("0")
    )
    total: Mapped[Decimal | None] = mapped_column("ThanhTien", DECIMAL(18, 4), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        "ThoiDiemThem", DateTime, server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column("TrangThai", String(20), nullable=False, default="Ch\u1edd")
    __table_args__ = (Index("ix_CHI_TIET_ORDER_MaMon_MaOrder", "MaMon", "MaOrder"),)


class TableMoveLog(Base):
    __tablename__ = "LICH_SU_DOI_BAN"
    id: Mapped[int] = mapped_column(
        "MaLichSuDoiBan", BigInteger, primary_key=True, autoincrement=True
    )
    order_id: Mapped[int] = mapped_column(
        "MaOrder",
        ForeignKey("ORDER.MaOrder", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    from_table: Mapped[int | None] = mapped_column(
        "MaBanNguon",
        ForeignKey("BAN.MaBan", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    to_table: Mapped[int | None] = mapped_column(
        "MaBanDich",
        ForeignKey("BAN.MaBan", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    performed_by: Mapped[int | None] = mapped_column(
        "NguoiThucHien",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )


class PaymentTransaction(Base):
    __tablename__ = "GIAO_DICH_THANH_TOAN"
    id: Mapped[int] = mapped_column(
        "MaGiaoDichTT", BigInteger, primary_key=True, autoincrement=True
    )
    order_id: Mapped[int] = mapped_column(
        "MaOrder",
        ForeignKey("ORDER.MaOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column("SoTien", DECIMAL(18, 4), nullable=False)
    method: Mapped[str] = mapped_column(
        "PhuongThuc", String(20), nullable=False, default="Ti\u1ec1n m\u1eb7t"
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Ch\u1edd thanh to\u00e1n"
    )
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )
    qr_code: Mapped[str | None] = mapped_column("MaQR", String(500), nullable=True)
    qr_created_at: Mapped[datetime | None] = mapped_column("ThoiDiemTaoQR", DateTime, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column("ThoiDiemHetHan", DateTime, nullable=True)
    gateway_transaction_id: Mapped[str | None] = mapped_column(
        "MaGiaoDichCong", String(100), nullable=True
    )
    webhook_content: Mapped[str | None] = mapped_column(
        "NoiDungWebhook", String(2000), nullable=True
    )
    bank_ref: Mapped[str | None] = mapped_column("MaGiaoDichNganHang", String(100), nullable=True)
    evidence: Mapped[str | None] = mapped_column("AnhChungTu", String(500), nullable=True)
    __table_args__ = (Index("ix_GIAO_DICH_THANH_TOAN_MaOrder_TrangThai", "MaOrder", "TrangThai"),)


class Invoice(Base):
    __tablename__ = "HOA_DON"
    id: Mapped[int] = mapped_column("MaHoaDon", BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        "MaOrder",
        ForeignKey("ORDER.MaOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        unique=True,
    )
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
    issued_at: Mapped[datetime] = mapped_column(
        "ThoiDiemXuat", DateTime, server_default=func.now(), nullable=False
    )
    total: Mapped[Decimal] = mapped_column(
        "TongTien", DECIMAL(18, 4), nullable=False, default=Decimal("0")
    )
    print_count: Mapped[int] = mapped_column("SoLanIn", Integer, nullable=False, default=1)
    payment_transaction_id: Mapped[int | None] = mapped_column(
        "MaGiaoDichThanhToan",
        BigInteger,
        ForeignKey("GIAO_DICH_THANH_TOAN.MaGiaoDichTT", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    invoice_number: Mapped[str | None] = mapped_column("SoHoaDon", String(50), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(
        "PhuongThucThanhToan", String(20), nullable=True
    )
    issued_by: Mapped[int | None] = mapped_column(
        "NguoiLap",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    __table_args__ = (Index("ix_HOA_DON_ThoiDiemXuat", "ThoiDiemXuat"),)


class KitchenTicket(Base):
    __tablename__ = "PHIEU_BEP"
    id: Mapped[int] = mapped_column("MaPhieuBep", BigInteger, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        "MaOrder",
        ForeignKey("ORDER.MaOrder", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    content: Mapped[str | None] = mapped_column("NoiDung", String(2000), nullable=True)
    print_status: Mapped[str] = mapped_column(
        "TrangThaiIn", String(20), nullable=False, default="Ch\u1edd in"
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Ch\u1edd in"
    )
    print_count: Mapped[int] = mapped_column("SoLanIn", Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )
