"""Schemas for Module 5 Settings."""

from datetime import datetime, time
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.shared.roles import Role

Username = Annotated[str, StringConstraints(min_length=3, max_length=50)]
Password = Annotated[str, StringConstraints(min_length=6, max_length=100)]


class LoginRequest(BaseModel):
    username: Username
    password: Password


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    MaNguoiDung: int = Field(validation_alias="id")
    TenDangNhap: str = Field(validation_alias="username")
    HoTen: str = Field(validation_alias="full_name")
    SoDienThoai: str | None = Field(default=None, validation_alias="phone")
    MaVaiTro: str = Field(validation_alias="role_id")
    TrangThai: str = Field(validation_alias="status")
    NgayTao: datetime = Field(validation_alias="created_at")

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserCreate(BaseModel):
    username: Username
    password: Password
    full_name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    phone: Annotated[str | None, StringConstraints(max_length=20)] = None
    role: Role


class UserUpdate(BaseModel):
    full_name: Annotated[str | None, StringConstraints(min_length=1, max_length=100)] = None
    phone: Annotated[str | None, StringConstraints(max_length=20)] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: Password


class ResetPasswordRequest(BaseModel):
    new_password: Password


class ConfigOut(BaseModel):
    MaCauHinh: int = Field(validation_alias="id")
    TenNhaHang: str = Field(validation_alias="restaurant_name")
    DiaChi: str | None = Field(default=None, validation_alias="address")
    MauHoaDon: str | None = Field(default=None, validation_alias="invoice_template")
    NguongTonMacDinh: int = Field(validation_alias="default_stock_threshold")
    GioBatDauBusinessDate: time = Field(validation_alias="business_day_start")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ConfigUpdate(BaseModel):
    TenNhaHang: Annotated[str | None, StringConstraints(min_length=1, max_length=100)] = None
    DiaChi: Annotated[str | None, StringConstraints(max_length=255)] = None
    MauHoaDon: Annotated[str | None, StringConstraints(max_length=50)] = None
    NguongTonMacDinh: int | None = Field(default=None, ge=0)
    # GioBatDauBusinessDate is fixed at 06:00, not editable via API


class BackupDump(BaseModel):
    created_at: datetime
    covers_until: datetime
    tables: list[str]


class AuditEntryOut(BaseModel):
    MaNhatKy: int = Field(validation_alias="id")
    MaNguoiDung: int = Field(validation_alias="user_id")
    ThoiDiem: datetime = Field(validation_alias="occurred_at")
    LoaiThaoTac: str = Field(validation_alias="action")
    DoiTuong: str = Field(validation_alias="target_entity")
    MaDoiTuong: str = Field(validation_alias="target_id")
    DuLieuTruoc: dict | None = Field(default=None, validation_alias="before")
    DuLieuSau: dict | None = Field(default=None, validation_alias="after")
    LyDo: str | None = Field(default=None, validation_alias="reason")

    model_config = {"from_attributes": True, "populate_by_name": True}
