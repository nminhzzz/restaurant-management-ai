"""Response contract for the reporting module.

Money is `Decimal` on purpose: Pydantic serialises it to a JSON string, so a client
never sees a float-rounded figure (see the plan's data contract).
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PeriodOut(BaseModel):
    start: date
    end: date
    granularity: str


class RevenueBucketOut(BaseModel):
    key: str | int | None
    DoanhThu: Decimal
    SoDon: int


class RevenueOut(BaseModel):
    total: Decimal
    provisional: Decimal
    SoDon: int
    items: list[RevenueBucketOut]
    period: PeriodOut


class DishRankOut(BaseModel):
    MaMon: int
    TenMon: str
    SoLuong: int
    DoanhThu: Decimal


class DishRankListOut(BaseModel):
    items: list[DishRankOut]
    period: PeriodOut


class HourBucketOut(BaseModel):
    ThoiDiem: int
    SoDon: int
    DoanhThu: Decimal


class WeekdayBucketOut(BaseModel):
    Thu: int
    SoDon: int


class HourlyOut(BaseModel):
    items: list[HourBucketOut]
    by_weekday: list[WeekdayBucketOut]
    period: PeriodOut


class MarginOut(BaseModel):
    DoanhThu: Decimal
    GiaVon: Decimal
    BienLoiNhuanGop: Decimal


class CostBreakdownOut(BaseModel):
    NguyenLieu: Decimal
    HaoHut: Decimal
    TongGiaVon: Decimal
    TamTinh: bool
    SoDongChuaTinhGiaVon: int


class DishCostOut(BaseModel):
    MaMon: int
    TenMon: str
    GiaVon: Decimal


class DishCostListOut(BaseModel):
    items: list[DishCostOut]


class RevenueSummaryOut(BaseModel):
    DoanhThu: Decimal
    GiaVon: Decimal
    SoDon: int


class ComparisonOut(BaseModel):
    left: RevenueSummaryOut
    right: RevenueSummaryOut
    change_percent: Decimal | None
    change_cost_percent: Decimal | None


class CancelledOrderOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str | None
    TongTien: Decimal
    GiaVon: Decimal
    LyDoHuy: str | None


class PendingPaymentOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str | None
    MaGiaoDich: int
    PhuongThuc: str
    SoTien: Decimal
    TrangThai: str
    ThoiGianChoPhut: int
    KetQuaGanNhat: str | None


class PendingPaymentListOut(BaseModel):
    items: list[PendingPaymentOut]


class CancelledReportOut(BaseModel):
    SoLuong: int
    TongGiaTri: Decimal
    TongGiaVon: Decimal
    items: list[CancelledOrderOut]


class ClosedUnpaidOrderOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str | None
    TongTien: Decimal
    GiaVon: Decimal
    LyDo: str | None


class ClosedUnpaidReportOut(BaseModel):
    SoLuong: int
    TongGiaTri: Decimal
    TongGiaVon: Decimal
    items: list[ClosedUnpaidOrderOut]
