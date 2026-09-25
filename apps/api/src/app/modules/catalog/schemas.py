"""Schemas for Module 1 Catalogue (Phase 2)."""

from datetime import date
from decimal import Decimal
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(min_length=1, max_length=100)]


def _validate_image_url(value: str | None) -> str | None:
    """HinhAnh is rendered in <img src>: only http(s) URLs or site-relative
    paths are accepted, never a `javascript:`/`data:` scheme or similar."""
    if value is None:
        return None
    v = value.strip()
    if v == "":
        return None
    parsed = urlparse(v)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return v
    if v.startswith("/") and not v.startswith("//"):
        return v
    raise ValueError("HinhAnh phải là URL http(s) hoặc đường dẫn nội bộ hợp lệ.")


class GroupCreate(BaseModel):
    TenNhom: Name
    ThuTuHienThi: int | None = Field(default=None, ge=1)


class GroupUpdate(BaseModel):
    TenNhom: Name | None = None


class GroupOut(BaseModel):
    MaNhomMon: int = Field(validation_alias="id")
    TenNhom: str = Field(validation_alias="name")
    ThuTuHienThi: int = Field(validation_alias="display_order")
    DaXoa: bool = Field(validation_alias="is_deleted")

    model_config = {"from_attributes": True, "populate_by_name": True}


class GroupReorderRequest(BaseModel):
    MaNhomMon: list[int] = Field(min_length=1)


class DishCreate(BaseModel):
    TenMon: Name
    MaNhomMon: int | None = None
    HinhAnh: str | None = Field(default=None, max_length=500)
    GiaHienTai: float | None = Field(default=None, ge=0)

    _check_hinh_anh = field_validator("HinhAnh")(_validate_image_url)


class DishUpdate(BaseModel):
    TenMon: Name | None = None
    MaNhomMon: int | None = None
    HinhAnh: str | None = Field(default=None, max_length=500)

    _check_hinh_anh = field_validator("HinhAnh")(_validate_image_url)


class DishOut(BaseModel):
    MaMon: int = Field(validation_alias="id")
    TenMon: str = Field(validation_alias="name")
    MaNhomMon: int | None = Field(default=None, validation_alias="group_id")
    HinhAnh: str | None = None
    GiaHienTai: float | None = None
    TrangThai: str
    AnThuCong: bool = Field(default=False, validation_alias="hide_manual")
    DaXoa: bool = Field(validation_alias="is_deleted")

    model_config = {"from_attributes": True, "populate_by_name": True}


class PriceScheduleRequest(BaseModel):
    Gia: Decimal = Field(ge=0)
    BusinessDateApDung: date | None = None


class PriceVersionOut(BaseModel):
    MaLichSuGia: int = Field(validation_alias="id")
    MaMon: int = Field(validation_alias="dish_id")
    Gia: float = Field(validation_alias="price")
    BusinessDateApDung: date = Field(validation_alias="business_date")
    TrangThai: str = Field(validation_alias="status")
    LoaiThayDoi: str = Field(validation_alias="change_type")

    model_config = {"from_attributes": True, "populate_by_name": True}


class PriceApplyNowRequest(BaseModel):
    Gia: Decimal = Field(ge=0)


class RecipeItemIn(BaseModel):
    MaNguyenLieu: int
    SoLuong: Decimal = Field(gt=0)


class RecipeScheduleRequest(BaseModel):
    BusinessDateApDung: date | None = None
    items: list[RecipeItemIn] = Field(min_length=1)


class RecipeAssignRequest(BaseModel):
    items: list[RecipeItemIn] = Field(min_length=1)


class RecipeApplyNowRequest(BaseModel):
    items: list[RecipeItemIn] = Field(min_length=1)


class RecipeOut(BaseModel):
    MaCongThuc: int = Field(validation_alias="id")
    MaMon: int = Field(validation_alias="dish_id")
    BusinessDateApDung: date = Field(validation_alias="business_date")
    TrangThai: str = Field(validation_alias="status")

    model_config = {"from_attributes": True, "populate_by_name": True}


class RecipeLineOut(BaseModel):
    MaNguyenLieu: int
    TenNguyenLieu: str
    SoLuong: float
    DonViTinh: str


class RecipeVersionOut(BaseModel):
    MaCongThuc: int
    MaMon: int
    BusinessDateApDung: date
    TrangThai: str
    LoaiThayDoi: str
    items: list[RecipeLineOut]


class IngredientCreate(BaseModel):
    TenNguyenLieu: Name
    DonViTinh: str | None = Field(default="kg", max_length=20)
    MucTonToiThieu: float | None = Field(default=None, ge=0)


class IngredientUpdate(BaseModel):
    TenNguyenLieu: Name | None = None
    DonViTinh: str | None = Field(default=None, max_length=20)
    MucTonToiThieu: float | None = Field(default=None, ge=0)


class IngredientOut(BaseModel):
    MaNguyenLieu: int = Field(validation_alias="id")
    TenNguyenLieu: str = Field(validation_alias="name")
    DonViTinh: str = Field(validation_alias="unit")
    MucTonToiThieu: float = Field(validation_alias="min_stock")
    DaXoa: bool = Field(validation_alias="is_deleted")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SupplierCreate(BaseModel):
    TenNhaCungCap: Name
    SoDienThoai: str | None = Field(default=None, max_length=20)


class SupplierUpdate(BaseModel):
    TenNhaCungCap: Name | None = None
    SoDienThoai: str | None = Field(default=None, max_length=20)


class SupplierOut(BaseModel):
    MaNhaCungCap: int = Field(validation_alias="id")
    TenNhaCungCap: str = Field(validation_alias="name")
    SoDienThoai: str | None = Field(default=None, validation_alias="phone")
    DaXoa: bool = Field(validation_alias="is_deleted")
    PhieuNhap: list[dict] = Field(default_factory=list)

    model_config = {"from_attributes": True, "populate_by_name": True}


class TableCreate(BaseModel):
    TenBan: Name


class TableOut(BaseModel):
    MaBan: int = Field(validation_alias="id")
    TenBan: str = Field(validation_alias="name")
    TrangThai: str = Field(validation_alias="status")
    DaXoa: bool = Field(validation_alias="is_deleted")

    model_config = {"from_attributes": True, "populate_by_name": True}


class VisibilityUpdate(BaseModel):
    AnThuCong: bool | None = None
    HetNLThuCong: bool | None = None
