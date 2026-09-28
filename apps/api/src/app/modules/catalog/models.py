"""Catalog module tables."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base, BigInteger


class DishGroup(Base):
    __tablename__ = "NHOM_MON"
    id: Mapped[int] = mapped_column("MaNhomMon", BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenNhomMon", String(100), nullable=False)
    display_order: Mapped[int] = mapped_column("ThuTuHienThi", Integer, nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column("NgayXoa", DateTime, nullable=True)


class Ingredient(Base):
    __tablename__ = "NGUYEN_LIEU"
    id: Mapped[int] = mapped_column(
        "MaNguyenLieu", BigInteger, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column("TenNguyenLieu", String(100), nullable=False)
    unit: Mapped[str] = mapped_column("DonViTinh", String(20), nullable=False, default="kg")
    stock_qty: Mapped[Decimal] = mapped_column(
        "SoLuongTon", DECIMAL(18, 4), nullable=False, default=Decimal("0")
    )
    version: Mapped[int] = mapped_column("Version", Integer, nullable=False, default=1)
    unit_locked: Mapped[bool] = mapped_column("DaKhoaDonVi", default=False, nullable=False)
    min_stock: Mapped[Decimal] = mapped_column(
        "MucTonToiThieu", DECIMAL(18, 4), nullable=False, default=Decimal("0")
    )
    shelf_days: Mapped[int | None] = mapped_column("SoNgayBaoQuan", Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("SoLuongTon >= 0", name="stock_non_negative"),
        CheckConstraint("MucTonToiThieu >= 0", name="min_stock_non_negative"),
    )


class Supplier(Base):
    __tablename__ = "NHA_CUNG_CAP"
    id: Mapped[int] = mapped_column("MaNCC", BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenNCC", String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column("DienThoai", String(20), nullable=True)
    contact_name: Mapped[str | None] = mapped_column("NguoiLienHe", String(100), nullable=True)
    email: Mapped[str | None] = mapped_column("Email", String(255), nullable=True)
    address: Mapped[str | None] = mapped_column("DiaChi", String(255), nullable=True)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)


class DiningTable(Base):
    __tablename__ = "BAN"
    id: Mapped[int] = mapped_column("MaBan", BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenBan", String(50), nullable=False)
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Tr\u1ed1ng"
    )
    area: Mapped[str | None] = mapped_column("KhuVuc", String(100), nullable=True)
    capacity: Mapped[int | None] = mapped_column("SoChoNgoi", Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)
    active_name: Mapped[str | None] = mapped_column(
        "TenBan_Active",
        String(50),
        Computed("CASE WHEN DaXoa = 1 THEN NULL ELSE TenBan END", persisted=True),
        unique=True,
        nullable=True,
    )


class Dish(Base):
    __tablename__ = "MON_AN"
    id: Mapped[int] = mapped_column("MaMon", BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenMon", String(100), nullable=False)
    group_id: Mapped[int | None] = mapped_column(
        "MaNhomMon",
        BigInteger,
        ForeignKey("NHOM_MON.MaNhomMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    image_url: Mapped[str | None] = mapped_column("HinhAnh", String(500), nullable=True)
    missing_recipe: Mapped[bool] = mapped_column("ChuaCoCongThuc", default=True, nullable=False)
    out_of_stock: Mapped[bool] = mapped_column("HetNguyenLieu", default=False, nullable=False)
    status: Mapped[str | None] = mapped_column(
        "TrangThai",
        String(20),
        Computed(
            (
                "CASE WHEN ChuaCoCongThuc=1 THEN 'Nháp' WHEN HetNguyenLieu=1 "
                "THEN 'Hết nguyên liệu' ELSE 'Hoạt động' END"
            ),
            persisted=True,
        ),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)


class DishPriceVersion(Base):
    __tablename__ = "LICH_SU_GIA_MON"
    id: Mapped[int] = mapped_column(
        "MaPhienBanGia", BigInteger, primary_key=True, autoincrement=True
    )
    dish_id: Mapped[int] = mapped_column(
        "MaMon",
        BigInteger,
        ForeignKey("MON_AN.MaMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column("GiaBan", DECIMAL(18, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        "ThoiDiemTao", DateTime, server_default=func.now(), nullable=False
    )
    business_date: Mapped[date] = mapped_column("BusinessDateApDung", Date, nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(
        "ThoiDiemHieuLuc", DateTime, nullable=True
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        "ThoiDiemHetHieuLuc", DateTime, nullable=True
    )
    change_type: Mapped[str] = mapped_column(
        "LoaiThayDoi", String(20), nullable=False, default="Tạo mới"
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Chờ áp dụng"
    )
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )


class Recipe(Base):
    __tablename__ = "CONG_THUC"
    id: Mapped[int] = mapped_column("MaCongThuc", BigInteger, primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(
        "MaMon",
        BigInteger,
        ForeignKey("MON_AN.MaMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    business_date: Mapped[date] = mapped_column("BusinessDateApDung", Date, nullable=False)
    effective_from: Mapped[datetime | None] = mapped_column(
        "ThoiDiemHieuLuc", DateTime, nullable=True
    )
    effective_to: Mapped[datetime | None] = mapped_column(
        "ThoiDiemHetHieuLuc", DateTime, nullable=True
    )
    change_type: Mapped[str] = mapped_column(
        "LoaiThayDoi", String(20), nullable=False, default="Tạo mới"
    )
    status: Mapped[str] = mapped_column(
        "TrangThai", String(20), nullable=False, default="Chờ áp dụng"
    )
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        BigInteger,
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    version_number: Mapped[int] = mapped_column("SoPhienBan", Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        "ThoiDiemTao", DateTime, server_default=func.now(), nullable=False
    )


class RecipeItem(Base):
    __tablename__ = "CHI_TIET_CONG_THUC"
    recipe_id: Mapped[int] = mapped_column(
        "MaCongThuc",
        BigInteger,
        ForeignKey("CONG_THUC.MaCongThuc", ondelete="CASCADE", onupdate="RESTRICT"),
        primary_key=True,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        BigInteger,
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    quantity: Mapped[Decimal] = mapped_column("DinhLuong", DECIMAL(18, 4), nullable=False)
