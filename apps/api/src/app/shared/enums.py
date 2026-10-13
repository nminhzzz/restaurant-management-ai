"""Shared business enums - StrEnum with Vietnamese DB values.

Only enums the code actually uses live here; each one lists the values of the
report's attribute table (appendix D).
"""

from enum import StrEnum


class UserStatus(StrEnum):
    HOAT_DONG = "Hoạt động"
    DA_KHOA = "Đã khóa"


class DishStatus(StrEnum):
    # MON_AN.TrangThai is derived from the recipe flag, stock and the manual pause (FR-CAT-27).
    NHAP = "Nháp"
    HOAT_DONG = "Hoạt động"
    HET_NGUYEN_LIEU = "Hết nguyên liệu"
    TAM_DUNG = "Tạm dừng phục vụ"


class OrderStatus(StrEnum):
    DANG_MO = "Đang mở"
    CHO_XAC_NHAN_THANH_TOAN = "Chờ xác nhận thanh toán"
    DA_THANH_TOAN = "Đã thanh toán"
    CHO_XAC_MINH_THANH_TOAN = "Chờ xác minh thanh toán"
    # The en dash is part of the state's name in the report (appendix D, ORDER.TrangThai).
    DONG_CHUA_THU_DUOC_TIEN = "Đóng – chưa thu được tiền"  # noqa: RUF001
    DA_HUY = "Đã hủy"
    TU_DONG_DONG = "Tự động đóng"


class VersionStatus(StrEnum):
    NHAP = "Chờ áp dụng"
    HIEU_LUC = "Đang áp dụng"
    HET_HIEU_LUC = "Hết hiệu lực"
    DA_HUY = "Đã hủy"


class ReceiptStatus(StrEnum):
    # A receipt stays "Nháp" (still correctable, FR-INV-02) until it is cancelled.
    NHAP = "Nháp"
    DA_HUY = "Đã hủy"


class LotStatus(StrEnum):
    CON_HAN = "Còn hạn"
    SAP_HET_HAN = "Sắp hết hạn"
    HET_HAN = "Hết hạn"
    DA_DUNG_HET = "Đã dùng hết"


class StockIssueSource(StrEnum):
    # PHIEU_XUAT_KHO.NguonXuat (FR-INV-05): only the first one books a manual movement.
    NGUYEN_LIEU = "Nguyên liệu"
    MON_DA_CHE_BIEN = "Món đã chế biến"
    KIEM_KE = "Kiểm kê"


class StocktakeStatus(StrEnum):
    DANG_KIEM_KE = "Đang kiểm kê"
    DA_CHOT = "Đã chốt"
    DA_HUY = "Đã hủy"


class StockMovementType(StrEnum):
    NHAP = "Nhập"
    TRU_TU_DONG = "Trừ tự động"
    HOAN_KHO = "Hoàn kho"
    XUAT_THU_CONG = "Xuất thủ công"
    DIEU_CHINH_KIEM_KE = "Điều chỉnh kiểm kê"


class TableStatus(StrEnum):
    TRONG = "Trống"
    DANG_PHUC_VU = "Đang phục vụ"


class OrderLineStatus(StrEnum):
    CHO_LAM = "Chờ làm"
    DA_XAC_NHAN_XONG = "Đã xác nhận xong"
    DA_PHUC_VU = "Đã phục vụ"
    DA_HUY = "Đã hủy"


class PaymentMethod(StrEnum):
    TIEN_MAT = "Tiền mặt"
    QR = "QR"


class PaymentStatus(StrEnum):
    CHO_XAC_NHAN = "Chờ xác nhận"
    THANH_CONG = "Thành công"
    HET_HAN = "Hết hạn"
    CHO_XAC_MINH = "Chờ xác minh thanh toán"
    # The en dash is part of the state's name in the report (appendix D, GIAO_DICH_THANH_TOAN).
    DONG_CHUA_THU_DUOC_TIEN = "Đóng – chưa thu được tiền"  # noqa: RUF001
    DA_HUY = "Đã hủy"


class PaymentExceptionStatus(StrEnum):
    CHO_XU_LY = "Chờ xử lý"
    DA_HOAN_TIEN = "Đã hoàn tiền"
    DA_AP_DUNG = "Đã áp dụng cho order"


class OrderType(StrEnum):
    TAI_CHO = "Tại chỗ"
    MANG_VE = "Mang về"
