"""Schemas for Module 5 Settings."""

from datetime import datetime, time
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

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
    MaNguoiDung: int
    TenDangNhap: str
    HoTen: str
    SoDienThoai: str | None = None
    MaVaiTro: str
    TrangThai: str
    NgayTao: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: Username
    password: Password
    full_name: Annotated[str, StringConstraints(min_length=1, max_length=100)]
    phone: Annotated[str | None, StringConstraints(max_length=20)] = None
    role: Annotated[str, StringConstraints(min_length=1)]


class UserUpdate(BaseModel):
    full_name: Annotated[str | None, StringConstraints(min_length=1, max_length=100)] = None
    phone: Annotated[str | None, StringConstraints(max_length=20)] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: Password


class ResetPasswordRequest(BaseModel):
    new_password: Password


class ConfigOut(BaseModel):
    MaCauHinh: int
    TenNhaHang: str
    DiaChi: str | None = None
    MauHoaDon: str | None = None
    NguongTonMacDinh: int
    GioBatDauBusinessDate: time

    model_config = {"from_attributes": True}


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
    MaNhatKy: int
    MaNguoiDung: int
    ThoiDiem: datetime
    LoaiThaoTac: str
    DoiTuong: str
    MaDoiTuong: str
    DuLieuTruoc: dict | None = None
    DuLieuSau: dict | None = None
    LyDo: str | None = None

    model_config = {"from_attributes": True}
