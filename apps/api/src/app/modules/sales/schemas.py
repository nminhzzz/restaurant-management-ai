"""Schemas for sales module — Task 1."""

from pydantic import BaseModel, Field


class OrderLineIn(BaseModel):
    dish_id: int = Field(alias="MaMon")
    quantity: int = Field(default=1, ge=1, alias="SoLuong")
    note: str | None = Field(default=None, alias="GhiChu")
    model_config = {"populate_by_name": True}


class SubmitOrderIn(BaseModel):
    table_id: int | None = Field(default=None, alias="MaBan")
    order_type: str = Field(default="Tại chỗ", alias="LoaiDon")
    lines: list[OrderLineIn] = Field(min_length=1)
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


class UpdateLineIn(BaseModel):
    quantity: int = Field(ge=1)


class CreateSelectionIn(BaseModel):
    selection_id: str | None = Field(default=None, max_length=64, alias="MaLuotChon")
    table_id: int | None = Field(default=None, alias="MaBan")
    order_id: int | None = Field(default=None, alias="MaOrder")
    model_config = {"populate_by_name": True}


class UpsertSelectionLineIn(BaseModel):
    quantity: int = Field(ge=1, alias="SoLuong")
    note: str | None = Field(default=None, max_length=500, alias="GhiChu")
    table_id: int | None = Field(default=None, alias="MaBan")
    order_id: int | None = Field(default=None, alias="MaOrder")
    model_config = {"populate_by_name": True}


class SubmitSelectionIn(BaseModel):
    send_request_id: str = Field(min_length=1, max_length=100, alias="MaYeuCauGui")
    model_config = {"populate_by_name": True}
