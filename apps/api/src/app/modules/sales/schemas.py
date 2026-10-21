"""Schemas for sales module — Task 1."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReleaseTableIn(BaseModel):
    order_id: int | None = Field(..., gt=0)


class OrderLineIn(BaseModel):
    dish_id: int = Field(alias="MaMon")
    quantity: int = Field(default=1, ge=1, alias="SoLuong")
    note: str | None = Field(default=None, alias="GhiChu")
    hold_id: int | None = None
    model_config = {"populate_by_name": True}


class SubmitOrderIn(BaseModel):
    table_id: int | None = Field(default=None, alias="MaBan")
    order_type: str = Field(default="Tại chỗ", alias="LoaiDon")
    lines: list[OrderLineIn] = Field(min_length=1)
    request_id: str | None = Field(default=None, max_length=36)
    confirm_expired: bool = Field(default=False, alias="XacNhanHetHan")
    model_config = {"populate_by_name": True}


class OrderLineOut(BaseModel):
    MaChiTietOrder: int
    MaMon: int
    SoLuong: int
    DonGia: float
    MaPhienBanGia: int | None = None
    MaCongThuc: int | None = None
    GhiChu: str | None = None
    TrangThai: str


class SubmitOrderOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str
    MaBan: int | None
    TrangThai: str
    lines: list[OrderLineOut]
    rejected: list[dict] = []


class AddLineIn(BaseModel):
    dish_id: int
    quantity: int = Field(ge=1)
    note: str | None = None
    hold_id: int | None = None
    request_line_id: str | None = Field(default=None, max_length=36)


class AddLinesIn(BaseModel):
    lines: list[AddLineIn] = Field(min_length=1)
    confirm_expired: bool = Field(default=False, alias="XacNhanHetHan")
    model_config = {"populate_by_name": True}


class UpdateLineIn(BaseModel):
    quantity: int = Field(ge=1)


class HoldCreate(BaseModel):
    selection_code: str | None = Field(default=None, max_length=36)
    table_id: int | None = None
    order_id: int | None = None
    dish_id: int
    quantity: int = Field(default=1, ge=1)
    note: str | None = Field(default=None, max_length=500)


class HoldUpdate(BaseModel):
    quantity: int = Field(ge=1)


class HoldOut(BaseModel):
    MaGiuCho: int
    MaLuotChon: str
    MaBan: int | None
    MaMon: int
    TenMon: str | None = None
    SoLuong: int
    GhiChu: str | None
    ThoiDiemHetHan: datetime
    TrangThai: str
    DonGia: float | None = None
    MaPhienBanGia: int | None = None
    MaCongThuc: int | None = None
