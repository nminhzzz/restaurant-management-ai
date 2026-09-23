"""Shared business enums - StrEnum with Vietnamese DB values."""

from enum import StrEnum


class UserStatus(StrEnum):
    HOAT_DONG = "Hoạt động"
    DA_KHOA = "Đã khóa"


class DishStatus(StrEnum):
    NHAP = "Nháp"
    HOAT_DONG = "Hoạt động"
    HET_NGUYEN_LIEU = "Hết nguyên liệu"
    AN_THU_CONG = "Ẩn thủ công"


class OrderStatus(StrEnum):
    CHO_XAC_NHAN = "Chờ xác nhận"
    DANG_CHE_BIEN = "Đang chế biến"
    DA_PHUC_VU = "Đã phục vụ"
    DA_THANH_TOAN = "Đã thanh toán"
    DA_HUY = "Đã hủy"


class OrderLineStatus(StrEnum):
    CHO = "Chờ"
    DA_XAC_NHAN = "Đã xác nhận"
    DANG_LAM = "Đang làm"
    DA_PHUC_VU = "Đã phục vụ"
    DA_HUY = "Đã hủy"


class PaymentStatus(StrEnum):
    CHO_THANH_TOAN = "Chờ thanh toán"
    DA_THANH_TOAN = "Đã thanh toán"
    THAT_BAI = "Thất bại"
    HOAN_TIEN = "Hoàn tiền"


class PrintStatus(StrEnum):
    CHO_IN = "Chờ in"
    DA_IN = "Đã in"
    LOI = "Lỗi"


class VersionStatus(StrEnum):
    NHAP = "Nháp"
    HIEU_LUC = "Hiệu lực"
    HET_HIEU_LUC = "Hết hiệu lực"


class ChangeType(StrEnum):
    TAO_MOI = "Tạo mới"
    CAP_NHAT = "Cập nhật"
    XOA = "Xóa"


class ReceiptStatus(StrEnum):
    NHAP = "Nháp"
    DA_NHAP = "Đã nhập"
    DA_HUY = "Đã hủy"


class LotStatus(StrEnum):
    CON_HAN = "Còn hạn"
    HET_HAN = "Hết hạn"
    DA_HUY = "Đã hủy"


class StocktakeStatus(StrEnum):
    NHAP = "Nháp"
    DA_CHOT = "Đã chốt"
    DA_HUY = "Đã hủy"


class StockMovementType(StrEnum):
    NHAP = "Nhập"
    TRU_TU_DONG = "Trừ tự động"
    HOAN_KHO = "Hoàn kho"
    XUAT_THU_CONG = "Xuất thủ công"
    DIEU_CHINH_KIEM_KE = "Điều chỉnh kiểm kê"


class WriteOffReason(StrEnum):
    HET_HAN = "Hết hạn"
    HU_HONG = "Hư hỏng"
    KHAC = "Khác"


class TableStatus(StrEnum):
    TRONG = "Trống"
    DANG_PHUC_VU = "Đang phục vụ"
    DA_DAT = "Đã đặt"


class AssistantTurnStatus(StrEnum):
    THANH_CONG = "Thành công"
    THAT_BAI = "Thất bại"
    TU_CHOI = "Từ chối"


# Alias for inventory movement kind (same values as StockMovementType, used by GIAO_DICH_KHO check)
StockMovementKind = StockMovementType
