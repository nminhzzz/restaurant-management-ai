"""Schemas for inventory."""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Name = Annotated[str, StringConstraints(min_length=1, max_length=100)]


class ReceiptLineIn(BaseModel):
    ingredient_id: int = Field(alias="ingredient_id")
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    purchase_unit: str | None = None
    conversion_factor: float | None = Field(default=None, gt=0)
    model_config = {"populate_by_name": True}


class ReceiptCreate(BaseModel):
    supplier_id: int | None = None
    receipt_date: datetime | None = None
    lines: list[ReceiptLineIn] = Field(min_length=1, max_length=100)


class ReceiptLineUpdateIn(BaseModel):
    line_id: int
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)


class ReceiptUpdate(BaseModel):
    lines: list[ReceiptLineUpdateIn] = Field(min_length=1, max_length=100)


class ReceiptOut(BaseModel):
    MaPhieuNhap: int
    model_config = ConfigDict(from_attributes=True)


class IssueLineIn(BaseModel):
    ingredient_id: int
    quantity: float = Field(gt=0)


class IssueCreate(BaseModel):
    reason: str = Field(default="Hao hụt")
    lines: list[IssueLineIn] = Field(min_length=1, max_length=100)


class StocktakeCreate(BaseModel):
    pass


class CountIn(BaseModel):
    ingredient_id: int
    actual_qty: float = Field(ge=0)


class MonthCostOut(BaseModel):
    MaNguyenLieu: int
    Thang: int
    GiaBinhQuan: float
    TongSoLuongNhap: float
    ThoiDiemTinh: datetime | None = None
    model_config = ConfigDict(from_attributes=True)


class StockRowOut(BaseModel):
    MaNguyenLieu: int
    TenNguyenLieu: str
    SoLuongTon: float
    MucTonToiThieuApDung: float
    CanhBaoTonThap: bool
