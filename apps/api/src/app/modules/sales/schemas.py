"""Request bodies of the sales API.

Vietnamese field names are the contract (report appendix D); the English names the first
version of the API used are still accepted so existing callers keep working. Every number and
text is bounded here, before a service runs (NFR-05).
"""

from decimal import Decimal
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

_NOTE = 255


class _Body(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class OrderLineIn(_Body):
    dish_id: int = Field(ge=1, alias="MaMon")
    quantity: int = Field(default=1, ge=1, le=999, alias="SoLuong")
    note: str | None = Field(default=None, max_length=500, alias="GhiChu")


class SubmitOrderIn(_Body):
    table_id: int | None = Field(default=None, ge=1, alias="MaBan")
    order_type: Literal["Tại chỗ", "Mang về"] = Field(default="Tại chỗ", alias="LoaiDon")
    lines: list[OrderLineIn] = Field(min_length=1, max_length=100)


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


class AddLineIn(_Body):
    dish_id: int = Field(ge=1, alias="MaMon")
    quantity: int = Field(default=1, ge=1, le=999, alias="SoLuong")
    note: str | None = Field(default=None, max_length=500, alias="GhiChu")


class UpdateLineIn(_Body):
    quantity: int = Field(ge=1, le=999, alias="SoLuong")


class LineStatusIn(_Body):
    to_status: str = Field(
        max_length=30, validation_alias=AliasChoices("TrangThai", "to", "to_status")
    )


class CancelLineIn(_Body):
    reason: str = Field(
        min_length=1, max_length=_NOTE, validation_alias=AliasChoices("LyDo", "reason")
    )


class MoveTableIn(_Body):
    to_table_id: int = Field(ge=1, validation_alias=AliasChoices("MaBanDich", "to_table_id", "to"))


class CancelOrderIn(_Body):
    reason: str = Field(
        min_length=1, max_length=_NOTE, validation_alias=AliasChoices("LyDoHuy", "reason")
    )
    guests_left: bool = Field(
        default=False, validation_alias=AliasChoices("KhachDaRoiDi", "guests_left")
    )


class PrintResultIn(_Body):
    ok: bool = True


class CreateSelectionIn(_Body):
    selection_id: str | None = Field(default=None, max_length=64, alias="MaLuotChon")
    table_id: int | None = Field(default=None, alias="MaBan")
    order_id: int | None = Field(default=None, alias="MaOrder")


class UpsertSelectionLineIn(_Body):
    quantity: int = Field(ge=1, le=999, alias="SoLuong")
    note: str | None = Field(default=None, max_length=500, alias="GhiChu")
    table_id: int | None = Field(default=None, alias="MaBan")
    order_id: int | None = Field(default=None, alias="MaOrder")


class SubmitSelectionIn(_Body):
    send_request_id: str = Field(min_length=1, max_length=100, alias="MaYeuCauGui")


# --- payments ------------------------------------------------------------------------------------


class VerificationRequestIn(_Body):
    """FR-SALE-19: what the guest gave the cashier. At least a reference or a note."""

    bank_reference: str | None = Field(default=None, max_length=100, alias="MaGiaoDichNganHang")
    evidence: str | None = Field(default=None, max_length=500, alias="AnhChungTu")
    note: str | None = Field(default=None, max_length=_NOTE, alias="GhiChu")


class VerificationNoteIn(_Body):
    """FR-SALE-20/34: a check result or extra evidence added while the order waits."""

    note: str = Field(min_length=1, max_length=_NOTE, alias="GhiChu")
    bank_reference: str | None = Field(default=None, max_length=100, alias="MaGiaoDichNganHang")
    evidence: str | None = Field(default=None, max_length=500, alias="AnhChungTu")


class ConfirmReceivedIn(_Body):
    note: str | None = Field(default=None, max_length=_NOTE, alias="GhiChu")
    bank_reference: str | None = Field(default=None, max_length=100, alias="MaGiaoDichNganHang")


class ManagerDecisionIn(_Body):
    """FR-SALE-23/35: why, and what was agreed outside the system."""

    reason: str = Field(min_length=1, max_length=_NOTE, alias="LyDo")
    outcome: str = Field(min_length=1, max_length=_NOTE, alias="KetQuaXuLy")


class ApplyExceptionIn(_Body):
    note: str | None = Field(default=None, max_length=_NOTE, alias="GhiChu")


class RefundExceptionIn(_Body):
    refund_reference: str = Field(min_length=1, max_length=100, alias="MaThamChieuHoan")
    note: str | None = Field(default=None, max_length=_NOTE, alias="GhiChu")


class SimulatorWebhookIn(_Body):
    payment_id: int = Field(ge=1, validation_alias=AliasChoices("MaGiaoDich", "payment_id"))
    amount: Decimal = Field(
        gt=0, max_digits=18, decimal_places=4, validation_alias=AliasChoices("SoTien", "amount")
    )
    signature: str = Field(max_length=128, validation_alias=AliasChoices("ChuKy", "signature"))
