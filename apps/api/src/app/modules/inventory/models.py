"""Inventory module tables."""

from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    BigInteger,
    CheckConstraint,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class GoodsReceipt(Base):
    __tablename__ = "PHIEU_NHAP_KHO"
    id: Mapped[int] = mapped_column("MaPhieuNhap", BigInteger, primary_key=True, autoincrement=True)
    receipt_date: Mapped[datetime] = mapped_column(
        "NgayNhap", DateTime, server_default=func.now(), nullable=False
    )
    supplier_id: Mapped[int | None] = mapped_column(
        "MaNhaCungCap",
        BigInteger,
        ForeignKey("NHA_CUNG_CAP.MaNhaCungCap", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Nh\u00e1p"
    )
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )


class GoodsReceiptLine(Base):
    __tablename__ = "CHI_TIET_PHIEU_NHAP"
    id: Mapped[int] = mapped_column(
        "MaChiTietNhap", BigInteger, primary_key=True, autoincrement=True
    )
    receipt_id: Mapped[int] = mapped_column(
        "MaPhieuNhap",
        BigInteger,
        ForeignKey("PHIEU_NHAP_KHO.MaPhieuNhap", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column("SoLuong", DECIMAL(18, 4), nullable=False)
    unit_price: Mapped[float] = mapped_column("DonGia", DECIMAL(18, 4), nullable=False)


class IngredientLot(Base):
    __tablename__ = "LO_NGUYEN_LIEU"
    id: Mapped[int] = mapped_column("MaLo", BigInteger, primary_key=True, autoincrement=True)
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    receipt_line_id: Mapped[int] = mapped_column(
        "MaChiTietNhap",
        BigInteger,
        ForeignKey("CHI_TIET_PHIEU_NHAP.MaChiTietNhap", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
        unique=True,
    )
    quantity_remaining: Mapped[float] = mapped_column(
        "SoLuongConLai", DECIMAL(18, 4), nullable=False
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="C\u00f2n h\u1ea1n"
    )
    received_at: Mapped[datetime] = mapped_column(
        "NgayNhap", DateTime, server_default=func.now(), nullable=False
    )
    is_adjustment: Mapped[bool] = mapped_column("LoDieuChinhKiemKe", default=False, nullable=False)
    __table_args__ = (
        Index(
            "ix_LO_NGUYEN_LIEU_MaNguyenLieu_TrangThai_NgayNhap",
            "MaNguyenLieu",
            "TrangThai",
            "NgayNhap",
        ),
    )


class StockIssue(Base):
    __tablename__ = "PHIEU_XUAT_KHO"
    id: Mapped[int] = mapped_column("MaPhieuXuat", BigInteger, primary_key=True, autoincrement=True)
    reason: Mapped[str] = mapped_column("LyDo", String(50), nullable=False, default="Kh\u00e1c")
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Nh\u00e1p"
    )
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )


class StockIssueLine(Base):
    __tablename__ = "CHI_TIET_PHIEU_XUAT"
    id: Mapped[int] = mapped_column(
        "MaChiTietXuat", BigInteger, primary_key=True, autoincrement=True
    )
    issue_id: Mapped[int] = mapped_column(
        "MaPhieuXuat",
        BigInteger,
        ForeignKey("PHIEU_XUAT_KHO.MaPhieuXuat", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[float] = mapped_column("SoLuong", DECIMAL(18, 4), nullable=False)
    estimated_cost: Mapped[float] = mapped_column(
        "GiaVonUocTinh", DECIMAL(18, 4), nullable=False, default=0
    )


class Stocktake(Base):
    __tablename__ = "PHIEU_KIEM_KE"
    id: Mapped[int] = mapped_column(
        "MaPhieuKiemKe", BigInteger, primary_key=True, autoincrement=True
    )
    stocktake_date: Mapped[datetime] = mapped_column(
        "NgayKiemKe", DateTime, server_default=func.now(), nullable=False
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Nh\u00e1p"
    )


class StocktakeLine(Base):
    __tablename__ = "CHI_TIET_KIEM_KE"
    id: Mapped[int] = mapped_column(
        "MaChiTietKiemKe", BigInteger, primary_key=True, autoincrement=True
    )
    stocktake_id: Mapped[int] = mapped_column(
        "MaPhieuKiemKe",
        BigInteger,
        ForeignKey("PHIEU_KIEM_KE.MaPhieuKiemKe", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    system_qty: Mapped[float] = mapped_column("TonHeThong", DECIMAL(18, 4), nullable=False)
    actual_qty: Mapped[float] = mapped_column("TonThucTe", DECIMAL(18, 4), nullable=False)
    difference: Mapped[float | None] = mapped_column(
        "ChenhLech",
        DECIMAL(18, 4),
        Computed("TonThucTe - TonHeThong", persisted=True),
        nullable=True,
    )


class StockMovement(Base):
    __tablename__ = "GIAO_DICH_KHO"
    id: Mapped[int] = mapped_column(
        "MaGiaoDichKho", BigInteger, primary_key=True, autoincrement=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    lot_id: Mapped[int | None] = mapped_column(
        "MaLoNguyenLieu",
        BigInteger,
        ForeignKey("LO_NGUYEN_LIEU.MaLo", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column("LoaiGiaoDich", String(30), nullable=False)
    qty: Mapped[float] = mapped_column("SoLuong", DECIMAL(18, 4), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    business_date: Mapped[datetime] = mapped_column("BusinessDate", DateTime, nullable=False)
    receipt_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietNhap",
        BigInteger,
        ForeignKey("CHI_TIET_PHIEU_NHAP.MaChiTietNhap", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    order_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietOrder",
        BigInteger,
        ForeignKey("CHI_TIET_ORDER.MaChiTietOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    issue_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietXuat",
        BigInteger,
        ForeignKey("CHI_TIET_PHIEU_XUAT.MaChiTietXuat", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    stocktake_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietKiemKe",
        BigInteger,
        ForeignKey("CHI_TIET_KIEM_KE.MaChiTietKiemKe", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    performed_by: Mapped[int | None] = mapped_column(
        "NguoiThucHien",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    __table_args__ = (
        CheckConstraint(
            "((LoaiGiaoDich = 'Nh\u1eadp' AND MaChiTietNhap IS NOT NULL) OR "
            "(LoaiGiaoDich IN ('Tr\u1eeb t\u1ef1 \u0111\u1ed9ng','Ho\u00e0n kho') AND MaChiTietOrder IS NOT NULL) OR "  # noqa: E501
            "(LoaiGiaoDich = 'Xu\u1ea5t th\u1ee7 c\u00f4ng' AND MaChiTietXuat IS NOT NULL) OR "
            "(LoaiGiaoDich = '\u0110i\u1ec1u ch\u1ec9nh ki\u1ec3m k\u00ea' AND MaChiTietKiemKe IS NOT NULL))",  # noqa: E501
            name="movement_source_matches_kind",
        ),
        Index("ix_GIAO_DICH_KHO_MaNguyenLieu_ThoiDiem", "MaNguyenLieu", "ThoiDiem"),
    )


class MonthlyAverageCost(Base):
    __tablename__ = "GIA_BINH_QUAN_THANG"
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    month: Mapped[int] = mapped_column("Thang", Integer, primary_key=True)
    avg_cost: Mapped[float] = mapped_column("GiaBinhQuan", DECIMAL(18, 4), nullable=False)
