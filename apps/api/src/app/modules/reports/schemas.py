"""Response contract for the reporting module.

Money is `Decimal` on purpose: Pydantic serialises it to a JSON string, so a client
never sees a float-rounded figure (see the plan's data contract).
"""

from datetime import date, datetime
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
    TieuHaoOrderHuy: Decimal
    TongGiaVon: Decimal
    TamTinh: bool
    SoDongChuaTinhGiaVon: int
    # Prepared dishes written off (FR-INV-05): already inside NguyenLieu/TieuHaoOrderHuy, so it
    # is shown for the reason analysis of FR-REP-05b and never added to TongGiaVon.
    MonDaCheBienBiHuy: Decimal = Decimal(0)


class DishCostOut(BaseModel):
    MaMon: int
    TenMon: str
    GiaVon: Decimal


class DishCostListOut(BaseModel):
    items: list[DishCostOut]


class PeriodFiguresOut(BaseModel):
    DoanhThu: Decimal
    SoDon: int
    GiaVon: Decimal


NO_PERCENTAGE = "Không xác định tỷ lệ phần trăm"


class ChangeOut(BaseModel):
    """FR-REP-08: absolute difference always; the percentage only when the base is not 0."""

    ChenhLechTuyetDoi: Decimal
    PhanTramChenhLech: Decimal | None
    GhiChu: str | None = None


class ComparisonOut(BaseModel):
    left: PeriodFiguresOut
    right: PeriodFiguresOut
    doanh_thu: ChangeOut
    chi_phi: ChangeOut
    change_percent: Decimal | None


class CancelledOrderOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str | None
    TongTien: Decimal
    LyDoHuy: str | None


class ClosedUnpaidOrderOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str | None
    SoTienChuaThu: Decimal
    GiaVonDaTieuHao: Decimal
    LyDo: str | None
    NguoiDong: int | None
    ThoiDiemDong: datetime | None


class ClosedUnpaidReportOut(BaseModel):
    SoLuong: int
    TongSoTienChuaThu: Decimal
    TongGiaVonDaTieuHao: Decimal
    items: list[ClosedUnpaidOrderOut]


class CancelledReportOut(BaseModel):
    SoLuong: int
    TongGiaTri: Decimal
    items: list[CancelledOrderOut]
    period: PeriodOut | None = None
    # The second group of FR-REP-10; its amounts are never added to the first group.
    DongChuaThuDuocTien: ClosedUnpaidReportOut | None = None


class UnsettledOrderOut(BaseModel):
    MaOrder: int
    MaOrderHienThi: str | None
    GiaTriOrder: Decimal
    ThoiDiemBatDauCho: datetime | None
    SoPhutDaCho: int | None
    KetQuaXuLyGanNhat: str | None


class UnsettledListOut(BaseModel):
    """FR-REP-02: waiting for verification; no invoice yet and not in revenue."""

    SoLuong: int
    TongGiaTri: Decimal
    items: list[UnsettledOrderOut]
