"""Sales module tables."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    DECIMAL,
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, BigInteger
from app.shared.business_date import local_now
from app.shared.enums import OrderLineStatus, PaymentMethod, PaymentStatus

# Every timestamp column below keeps its `server_default` (the migrations declare it) but the
# application always sends `local_now` (Asia/Ho_Chi_Minh), so no value depends on the DB server tz.


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
        "NgayTao", DateTime, default=local_now, server_default=func.now(), nullable=False
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
        "ThoiDiemThem", DateTime, default=local_now, server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default=OrderLineStatus.CHO_LAM.value
    )
    __table_args__ = (
        CheckConstraint("SoLuong > 0", name="quantity_positive"),
        Index("ix_CHI_TIET_ORDER_MaMon_MaOrder", "MaMon", "MaOrder"),
    )


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
        "ThoiDiem", DateTime, default=local_now, server_default=func.now(), nullable=False
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
        "PhuongThuc", String(20), nullable=False, default=PaymentMethod.TIEN_MAT.value
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(30), nullable=False, default=PaymentStatus.CHO_XAC_NHAN.value
    )
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, default=local_now, server_default=func.now(), nullable=False
    )
    qr_code: Mapped[str | None] = mapped_column("MaQR", String(500), nullable=True)
    qr_created_at: Mapped[datetime | None] = mapped_column("ThoiDiemTaoQR", DateTime, nullable=True)
    deadline: Mapped[datetime | None] = mapped_column("ThoiDiemHetHan", DateTime, nullable=True)
    gateway_transaction_id: Mapped[str | None] = mapped_column(
        "MaGiaoDichCong", String(100), nullable=True, unique=True
    )
    webhook_content: Mapped[str | None] = mapped_column(
        "NoiDungWebhook", String(2000), nullable=True
    )
    bank_ref: Mapped[str | None] = mapped_column(
        "MaGiaoDichNganHang", String(100), nullable=True, unique=True
    )
    evidence: Mapped[str | None] = mapped_column("AnhChungTu", String(500), nullable=True)
    exception_status: Mapped[str | None] = mapped_column(
        "TrangThaiNgoaiLe", String(30), nullable=True
    )
    exception_amount: Mapped[Decimal | None] = mapped_column(
        "SoTienNgoaiLe", DECIMAL(18, 4), nullable=True
    )
    refund_reference: Mapped[str | None] = mapped_column(
        "MaThamChieuHoan", String(100), nullable=True
    )
    exception_handled_at: Mapped[datetime | None] = mapped_column(
        "ThoiDiemXuLyNgoaiLe", DateTime, nullable=True
    )
    exception_handled_by: Mapped[int | None] = mapped_column(
        "NguoiXuLyNgoaiLe",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
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
        "ThoiDiemXuat", DateTime, default=local_now, server_default=func.now(), nullable=False
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
    invoice_number: Mapped[str | None] = mapped_column(
        "SoHoaDon", String(50), nullable=True, unique=True
    )
    payment_method: Mapped[str | None] = mapped_column(
        "PhuongThucThanhToan", String(20), nullable=True
    )
    issued_by: Mapped[int | None] = mapped_column(
        "NguoiLap",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    # The invoice as issued (restaurant, lines, names, totals); a reprint renders this content.
    content: Mapped[dict[str, Any] | None] = mapped_column("NoiDungHoaDon", JSON, nullable=True)
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
        "NgayTao", DateTime, default=local_now, server_default=func.now(), nullable=False
    )


class ItemHold(Base):
    __tablename__ = "GIU_CHO_MON"

    id: Mapped[int] = mapped_column("MaGiuCho", BigInteger, primary_key=True, autoincrement=True)
    selection_id: Mapped[str] = mapped_column("MaLuotChon", String(64), nullable=False)
    owner_id: Mapped[int] = mapped_column(
        "MaNguoiDung",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    table_id: Mapped[int | None] = mapped_column(
        "MaBan",
        BigInteger,
        ForeignKey("BAN.MaBan", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    order_id: Mapped[int | None] = mapped_column(
        "MaOrder",
        BigInteger,
        ForeignKey("ORDER.MaOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    dish_id: Mapped[int] = mapped_column(
        "MaMon",
        BigInteger,
        ForeignKey("MON_AN.MaMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    recipe_id: Mapped[int] = mapped_column(
        "MaCongThuc",
        BigInteger,
        ForeignKey("CONG_THUC.MaCongThuc", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    price_version_id: Mapped[int] = mapped_column(
        "MaPhienBanGia",
        BigInteger,
        ForeignKey("LICH_SU_GIA_MON.MaPhienBanGia", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column("SoLuong", Integer, nullable=False)
    note: Mapped[str | None] = mapped_column("GhiChu", String(500), nullable=True)
    expires_at: Mapped[datetime] = mapped_column("ThoiDiemHetHan", DateTime, nullable=False)
    status: Mapped[str] = mapped_column("TrangThai", String(20), nullable=False, default="Đang giữ")
    send_request_id: Mapped[str | None] = mapped_column("MaYeuCauGui", String(100), nullable=True)
    send_line_id: Mapped[str | None] = mapped_column("MaDongYeuCau", String(100), nullable=True)
    order_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietOrder",
        BigInteger,
        ForeignKey("CHI_TIET_ORDER.MaChiTietOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        unique=True,
    )

    __table_args__ = (
        CheckConstraint("SoLuong > 0", name="hold_quantity_positive"),
        UniqueConstraint("MaYeuCauGui", "MaDongYeuCau"),
        Index("ix_GIU_CHO_MON_MaLuotChon_TrangThai", "MaLuotChon", "TrangThai"),
        Index("ix_GIU_CHO_MON_TrangThai_ThoiDiemHetHan", "TrangThai", "ThoiDiemHetHan"),
    )


class ItemHoldLot(Base):
    __tablename__ = "CHI_TIET_GIU_CHO"

    hold_id: Mapped[int] = mapped_column(
        "MaGiuCho",
        BigInteger,
        ForeignKey("GIU_CHO_MON.MaGiuCho", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    lot_id: Mapped[int] = mapped_column(
        "MaLoNguyenLieu",
        BigInteger,
        ForeignKey("LO_NGUYEN_LIEU.MaLoNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    quantity_held: Mapped[Decimal] = mapped_column("SoLuongGiu", DECIMAL(18, 4), nullable=False)

    __table_args__ = (
        CheckConstraint("SoLuongGiu > 0", name="held_quantity_positive"),
        Index("ix_CHI_TIET_GIU_CHO_MaLoNguyenLieu_MaGiuCho", "MaLoNguyenLieu", "MaGiuCho"),
    )
