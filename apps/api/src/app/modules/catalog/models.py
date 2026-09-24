"""Catalog module tables."""

from datetime import date, datetime

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
    Computed,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base import Base


class DishGroup(Base):
    __tablename__ = "NHOM_MON"
    id: Mapped[int] = mapped_column("MaNhomMon", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenNhom", String(100), nullable=False)
    display_order: Mapped[int] = mapped_column("ThuTuHienThi", Integer, nullable=False, default=0)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)


class Ingredient(Base):
    __tablename__ = "NGUYEN_LIEU"
    id: Mapped[int] = mapped_column("MaNguyenLieu", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenNguyenLieu", String(100), nullable=False)
    unit: Mapped[str] = mapped_column("DonViTinh", String(20), nullable=False, default="kg")
    stock_qty: Mapped[float] = mapped_column(
        "SoLuongTon", DECIMAL(18, 4), nullable=False, default=0
    )
    version: Mapped[int] = mapped_column("Version", Integer, nullable=False, default=1)
    unit_locked: Mapped[bool] = mapped_column("DaKhoaDonVi", default=False, nullable=False)
    min_stock: Mapped[float] = mapped_column(
        "MucTonToiThieu", DECIMAL(18, 4), nullable=False, default=0
    )
    shelf_days: Mapped[int | None] = mapped_column("SoNgayBaoQuan", Integer, nullable=True)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)
    __table_args__ = (
        CheckConstraint("SoLuongTon >= 0", name="stock_non_negative"),
        CheckConstraint("MucTonToiThieu >= 0", name="min_stock_non_negative"),
    )


class Supplier(Base):
    __tablename__ = "NHA_CUNG_CAP"
    id: Mapped[int] = mapped_column("MaNhaCungCap", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenNhaCungCap", String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column("SoDienThoai", String(20), nullable=True)
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)


class DiningTable(Base):
    __tablename__ = "BAN"
    id: Mapped[int] = mapped_column("MaBan", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenBan", String(50), nullable=False)
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
    id: Mapped[int] = mapped_column("MaMon", primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column("TenMon", String(100), nullable=False)
    group_id: Mapped[int | None] = mapped_column(
        "MaNhomMon",
        ForeignKey("NHOM_MON.MaNhomMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )
    hide_manual: Mapped[bool] = mapped_column("AnThuCong", default=False, nullable=False)
    out_of_stock_manual: Mapped[bool] = mapped_column("HetNLThuCong", default=False, nullable=False)
    out_of_stock_auto: Mapped[bool] = mapped_column("HetNLTuDong", default=False, nullable=False)
    status: Mapped[str | None] = mapped_column(
        "TrangThai",
        String(20),
        Computed(
            (
                "CASE WHEN AnThuCong=1 THEN 'An' WHEN HetNLThuCong=1 OR "
                "HetNLTuDong=1 THEN 'Hết nguyên liệu' ELSE 'Hoạt động' END"
            ),
            persisted=True,
        ),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)


class DishPriceVersion(Base):
    __tablename__ = "LICH_SU_GIA_MON"
    id: Mapped[int] = mapped_column("MaLichSuGia", primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(
        "MaMon",
        ForeignKey("MON_AN.MaMon", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=False,
    )
    price: Mapped[float] = mapped_column("Gia", DECIMAL(18, 4), nullable=False)
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
    status: Mapped[str] = mapped_column("TrangThai", String(20), nullable=False, default="Nháp")
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )


class Recipe(Base):
    __tablename__ = "CONG_THUC"
    id: Mapped[int] = mapped_column("MaCongThuc", primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(
        "MaMon",
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
    status: Mapped[str] = mapped_column("TrangThai", String(20), nullable=False, default="Nháp")
    created_by: Mapped[int | None] = mapped_column(
        "NguoiTao",
        ForeignKey("NGUOI_DUNG.MaNguoiDung", ondelete="RESTRICT", onupdate="RESTRICT"),
        nullable=True,
    )


class RecipeItem(Base):
    __tablename__ = "CHI_TIET_CONG_THUC"
    recipe_id: Mapped[int] = mapped_column(
        "MaCongThuc",
        ForeignKey("CONG_THUC.MaCongThuc", ondelete="CASCADE", onupdate="RESTRICT"),
        primary_key=True,
    )
    ingredient_id: Mapped[int] = mapped_column(
        "MaNguyenLieu",
        ForeignKey("NGUYEN_LIEU.MaNguyenLieu", ondelete="RESTRICT", onupdate="RESTRICT"),
        primary_key=True,
    )
    quantity: Mapped[float] = mapped_column("SoLuong", DECIMAL(18, 4), nullable=False)
