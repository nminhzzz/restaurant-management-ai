"""Schemas for Module 1 Catalogue (Phase 2 Task 1)."""

from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

Name = Annotated[str, StringConstraints(min_length=1, max_length=100)]
Search = Annotated[str | None, StringConstraints(max_length=100)]


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


class DishUpdate(BaseModel):
    TenMon: Name | None = None
    MaNhomMon: int | None = None
    HinhAnh: str | None = Field(default=None, max_length=500)


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
