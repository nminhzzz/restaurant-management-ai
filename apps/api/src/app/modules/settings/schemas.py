"""Schemas for Module 5 Settings."""

from datetime import date, datetime, time
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints

from app.shared.roles import Role

# Upper bounds keep a typo from producing an absurd setting (a hold lasting years would
# overflow date arithmetic); the report only fixes the lower bounds (FR-SET-04).
MAX_STOCK_THRESHOLD = 1_000_000
MAX_EXPIRY_WARNING_DAYS = 365
MAX_AI_DAILY_QUESTIONS = 10_000
MAX_HOLD_MINUTES = 1_440

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
    role: Role | None = None

    model_config = {"extra": "forbid"}


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
    NguongTonMacDinh: float = Field(validation_alias="default_stock_threshold")
    GioBatDauBusinessDate: time = Field(validation_alias="business_day_start")
    GioBatDauBusinessDateMoi: time | None = Field(
        default=None, validation_alias="pending_business_day_start"
    )
    NgayHieuLucGioMoi: date | None = Field(
        default=None, validation_alias="pending_business_day_effective_date"
    )
    SoNgayCanhBaoHetHan: int = Field(validation_alias="expiry_warning_days")
    SoCauHoiAIMoiNgay: int = Field(validation_alias="ai_daily_question_quota")
    ThoiGianGiuChoPhut: int = Field(validation_alias="reservation_hold_minutes")

    model_config = {"from_attributes": True, "populate_by_name": True}


class ConfigUpdate(BaseModel):
    TenNhaHang: Annotated[str | None, StringConstraints(min_length=1, max_length=100)] = None
    DiaChi: Annotated[str | None, StringConstraints(max_length=255)] = None
    MauHoaDon: Annotated[str | None, StringConstraints(max_length=50)] = None
    NguongTonMacDinh: float | None = Field(default=None, ge=0, le=MAX_STOCK_THRESHOLD)
    GioBatDauBusinessDateMoi: time | None = None
    SoNgayCanhBaoHetHan: int | None = Field(default=None, gt=0, le=MAX_EXPIRY_WARNING_DAYS)
    SoCauHoiAIMoiNgay: int | None = Field(default=None, gt=0, le=MAX_AI_DAILY_QUESTIONS)
    ThoiGianGiuChoPhut: int | None = Field(default=None, gt=0, le=MAX_HOLD_MINUTES)


class BackupDump(BaseModel):
    created_at: datetime
    covers_until: datetime
    tables: list[str]
    data: dict[str, list[dict[str, Any]]]


class AuditEntryOut(BaseModel):
    MaNhatKy: int = Field(validation_alias="id")
    MaNguoiDung: int | None = Field(default=None, validation_alias="user_id")
    ThoiDiem: datetime = Field(validation_alias="occurred_at")
    LoaiThaoTac: str = Field(validation_alias="action")
    DoiTuong: str = Field(validation_alias="target_entity")
    MaDoiTuong: str = Field(validation_alias="target_id")
    DuLieuTruoc: dict | None = Field(default=None, validation_alias="before")
    DuLieuSau: dict | None = Field(default=None, validation_alias="after")
    LyDo: str | None = Field(default=None, validation_alias="reason")

    model_config = {"from_attributes": True, "populate_by_name": True}
