"""Inventory module tables."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, BigInteger


class GoodsReceipt(Base):
    __tablename__ = "PHIEU_NHAP_KHO"
    id: Mapped[int] = mapped_column("MaPhieuNhap", BigInteger, primary_key=True, autoincrement=True)
    receipt_date: Mapped[datetime] = mapped_column(
        "NgayNhap", DateTime, server_default=func.now(), nullable=False
    )
    supplier_id: Mapped[int | None] = mapped_column(
        "MaNCC",
        ForeignKey("NHA_CUNG_CAP.MaNCC", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Nh\u00e1p"
    )
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    total: Mapped[Decimal] = mapped_column("TongTien", DECIMAL(18, 4), nullable=False, default=0)
    note: Mapped[str | None] = mapped_column("GhiChu", String(500), nullable=True)


class GoodsReceiptLine(Base):
    __tablename__ = "CHI_TIET_PHIEU_NHAP"
    id: Mapped[int] = mapped_column(
        "MaChiTietNhap", BigInteger, primary_key=True, autoincrement=True
    )
    receipt_id: Mapped[int] = mapped_column(
        "MaPhieuNhap",
        ForeignKey("PHIEU_NHAP_KHO.MaPhieuNhap", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column("SoLuong", DECIMAL(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column("DonGia", DECIMAL(18, 4), nullable=False)
    original_purchase_unit: Mapped[str | None] = mapped_column(
        "DonViMuaGoc", String(20), nullable=True
    )
    conversion_factor: Mapped[Decimal] = mapped_column(
        "HeSoQuyDoi", DECIMAL(18, 4), nullable=False, default=1
    )
    total: Mapped[Decimal] = mapped_column("ThanhTien", DECIMAL(18, 4), nullable=False, default=0)
    __table_args__ = (
        CheckConstraint("SoLuong > 0", name="quantity_positive"),
        CheckConstraint("HeSoQuyDoi > 0", name="conversion_factor_positive"),
    )


def _received_quantity_default(context) -> Decimal:
    """A lot starts with what it was created with unless the caller says otherwise."""
    return context.get_current_parameters().get("SoLuongConLai", Decimal(0))


class IngredientLot(Base):
    __tablename__ = "LO_NGUYEN_LIEU"
    id: Mapped[int] = mapped_column(
        "MaLoNguyenLieu", BigInteger, primary_key=True, autoincrement=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    receipt_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietNhap",
        ForeignKey("CHI_TIET_PHIEU_NHAP.MaChiTietNhap", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
        unique=True,
    )
    quantity_remaining: Mapped[Decimal] = mapped_column(
        "SoLuongConLai", DECIMAL(18, 4), nullable=False
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="C\u00f2n h\u1ea1n"
    )
    received_at: Mapped[datetime] = mapped_column(
        "NgayNhap", DateTime, server_default=func.now(), nullable=False
    )
    is_adjustment: Mapped[bool] = mapped_column("LoDieuChinhKiemKe", default=False, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column("HanSuDung", Date, nullable=True)
    received_quantity: Mapped[Decimal] = mapped_column(
        "SoLuongNhap", DECIMAL(18, 4), nullable=False, default=_received_quantity_default
    )
    unit_price: Mapped[Decimal] = mapped_column("DonGia", DECIMAL(18, 4), nullable=False, default=0)
    __table_args__ = (
        CheckConstraint("SoLuongNhap > 0", name="received_quantity_positive"),
        CheckConstraint("SoLuongConLai >= 0", name="remaining_quantity_non_negative"),
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
    issue_date: Mapped[datetime | None] = mapped_column("NgayXuat", DateTime, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        "NguoiLap",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column("GhiChu", String(500), nullable=True)
    source: Mapped[str] = mapped_column(
        "NguonXuat", String(30), nullable=False, default="Nguy\u00ean li\u1ec7u"
    )
    # Set when the voucher was generated by confirming a stocktake (FR-INV-09, BR-LOT-02).
    stocktake_id: Mapped[int | None] = mapped_column(
        "MaPhieuKiemKe",
        BigInteger,
        ForeignKey("PHIEU_KIEM_KE.MaPhieuKiemKe", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    __table_args__ = (
        CheckConstraint(
            "NguonXuat IN ('Nguy\u00ean li\u1ec7u', 'M\u00f3n \u0111\u00e3 ch\u1ebf bi\u1ebfn', "
            "'Ki\u1ec3m k\u00ea')",
            name="source_known",
        ),
        CheckConstraint(
            "(NguonXuat = 'Ki\u1ec3m k\u00ea') = (MaPhieuKiemKe IS NOT NULL)",
            name="stocktake_source_matches_reference",
        ),
    )


class StockIssueLine(Base):
    __tablename__ = "CHI_TIET_PHIEU_XUAT"
    id: Mapped[int] = mapped_column(
        "MaChiTietXuat", BigInteger, primary_key=True, autoincrement=True
    )
    issue_id: Mapped[int] = mapped_column(
        "MaPhieuXuat",
        ForeignKey("PHIEU_XUAT_KHO.MaPhieuXuat", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column("SoLuong", DECIMAL(18, 4), nullable=False)
    estimated_cost: Mapped[Decimal] = mapped_column(
        "GiaVonUocTinh", DECIMAL(18, 4), nullable=False, default=0
    )
    order_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietOrder",
        BigInteger,
        ForeignKey("CHI_TIET_ORDER.MaChiTietOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    servings: Mapped[int | None] = mapped_column("SoSuatHuy", Integer, nullable=True)
    __table_args__ = (
        CheckConstraint("SoLuong > 0", name="quantity_positive"),
        CheckConstraint("SoSuatHuy IS NULL OR SoSuatHuy > 0", name="servings_positive"),
        CheckConstraint(
            "(MaChiTietOrder IS NULL) = (SoSuatHuy IS NULL)", name="dish_reference_complete"
        ),
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
        "TrangThai", String(20), nullable=False, default="\u0110ang ki\u1ec3m k\u00ea"
    )
    performed_by: Mapped[int | None] = mapped_column(
        "NguoiThucHien",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column("GhiChu", String(500), nullable=True)


class StocktakeLine(Base):
    __tablename__ = "CHI_TIET_KIEM_KE"
    id: Mapped[int] = mapped_column(
        "MaChiTietKiemKe", BigInteger, primary_key=True, autoincrement=True
    )
    stocktake_id: Mapped[int] = mapped_column(
        "MaPhieuKiemKe",
        ForeignKey("PHIEU_KIEM_KE.MaPhieuKiemKe", ondelete="CASCADE", onupdate="RESTRICT"),
        nullable=False,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    system_qty: Mapped[Decimal] = mapped_column("TonHeThong", DECIMAL(18, 4), nullable=False)
    actual_qty: Mapped[Decimal] = mapped_column("TonThucTe", DECIMAL(18, 4), nullable=False)
    difference: Mapped[Decimal | None] = mapped_column(
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
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    lot_id: Mapped[int | None] = mapped_column(
        "MaLoNguyenLieu",
        ForeignKey("LO_NGUYEN_LIEU.MaLoNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column("LoaiGiaoDich", String(30), nullable=False)
    qty: Mapped[Decimal] = mapped_column("SoLuongThayDoi", DECIMAL(18, 4), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        "ThoiDiem", DateTime, server_default=func.now(), nullable=False
    )
    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
    receipt_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietNhap",
        ForeignKey("CHI_TIET_PHIEU_NHAP.MaChiTietNhap", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    order_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietOrder",
        ForeignKey("CHI_TIET_ORDER.MaChiTietOrder", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    issue_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietXuat",
        ForeignKey("CHI_TIET_PHIEU_XUAT.MaChiTietXuat", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    stocktake_line_id: Mapped[int | None] = mapped_column(
        "MaChiTietKiemKe",
        ForeignKey("CHI_TIET_KIEM_KE.MaChiTietKiemKe", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    performed_by: Mapped[int | None] = mapped_column(
        "NguoiThucHien",
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    balance_after: Mapped[Decimal] = mapped_column(
        "TonSauGiaoDich", DECIMAL(18, 4), nullable=False, default=0
    )
    __table_args__ = (
        # Report section 3.2.2: each movement type is tied to its one source document.
        CheckConstraint(
            "((LoaiGiaoDich = 'Nh\u1eadp' AND MaChiTietNhap IS NOT NULL) OR "
            "(LoaiGiaoDich = 'Tr\u1eeb t\u1ef1 \u0111\u1ed9ng' AND MaChiTietOrder IS NOT NULL) OR "
            "(LoaiGiaoDich = 'Ho\u00e0n kho' AND MaChiTietOrder IS NOT NULL) OR "
            "(LoaiGiaoDich = 'Xu\u1ea5t th\u1ee7 c\u00f4ng' AND MaChiTietXuat IS NOT NULL) OR "
            "(LoaiGiaoDich = '\u0110i\u1ec1u ch\u1ec9nh ki\u1ec3m k\u00ea' "
            "AND MaChiTietKiemKe IS NOT NULL))",
            name="movement_source_matches_kind",
        ),
        Index("ix_GIAO_DICH_KHO_MaNguyenLieu_ThoiDiem", "MaNguyenLieu", "ThoiDiem"),
    )


class MonthlyAverageCost(Base):
    __tablename__ = "GIA_BINH_QUAN_THANG"
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    month: Mapped[int] = mapped_column("Thang", Integer, primary_key=True)
    avg_cost: Mapped[Decimal] = mapped_column("DonGiaBinhQuan", DECIMAL(18, 4), nullable=False)
    total_qty: Mapped[Decimal] = mapped_column(
        "TongSoLuongNhap", DECIMAL(18, 4), nullable=False, default=0
    )
    computed_at: Mapped[datetime] = mapped_column(
        "ThoiDiemTinh", DateTime, server_default=func.now(), nullable=False
    )
