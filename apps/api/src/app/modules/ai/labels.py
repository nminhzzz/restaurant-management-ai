"""Human labels and value kinds for the assistant's result columns.

Column names come from the `vw_ai_*` views or from aliases the model writes. Known
names get a Vietnamese label; anything else is split on CamelCase (no accents are
guessed) and typed from its name, then from its values.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

Kind = Literal["text", "money", "number", "date", "datetime", "percent"]

KNOWN: dict[str, tuple[str, Kind]] = {
    "BusinessDate": ("Ngày kinh doanh", "date"),
    "CanhBaoTonThap": ("Cảnh báo tồn thấp", "number"),
    "DonGiaMon": ("Đơn giá món", "money"),
    "DonGiaNhap": ("Đơn giá nhập", "money"),
    "DonViTinh": ("Đơn vị tính", "text"),
    "GiaBinhQuanThang": ("Giá bình quân tháng", "money"),
    "HanSuDungLo": ("Hạn sử dụng lô", "date"),
    "LoaiBanGhi": ("Loại bản ghi", "text"),
    "LoaiDon": ("Loại đơn", "text"),
    "LoaiGiaoDich": ("Loại giao dịch", "text"),
    "LyDoHuyOrder": ("Lý do hủy", "text"),
    "MaBan": ("Mã bàn", "text"),
    "MaGiaoDich": ("Mã giao dịch", "text"),
    "MaGiaoDichKho": ("Mã giao dịch kho", "text"),
    "MaHoaDon": ("Mã hoá đơn", "text"),
    "MaLo": ("Mã lô", "text"),
    "MaNguyenLieu": ("Mã nguyên liệu", "text"),
    "MaOrder": ("Mã order", "text"),
    "MaPhieuNhap": ("Mã phiếu nhập", "text"),
    "MucTonToiThieu": ("Mức tồn tối thiểu", "number"),
    "NgayNhapLo": ("Ngày nhập lô", "datetime"),
    "PhuongThuc": ("Phương thức", "text"),
    "SoLuong": ("Số lượng", "number"),
    "SoLuongConLai": ("Số lượng còn lại", "number"),
    "SoLuongMon": ("Số lượng món", "number"),
    "SoLuongNhap": ("Số lượng nhập", "number"),
    "SoLuongTon": ("Số lượng tồn", "number"),
    "SoTien": ("Số tiền", "money"),
    "TenMon": ("Tên món", "text"),
    "TenNguyenLieu": ("Tên nguyên liệu", "text"),
    "TenNhaCungCap": ("Nhà cung cấp", "text"),
    "TenNhom": ("Nhóm món", "text"),
    "Thang": ("Tháng", "text"),
    "ThanhTienMon": ("Thành tiền", "money"),
    "ThoiDiemXuat": ("Thời điểm xuất", "datetime"),
    "TongSoLuongNhapThang": ("Tổng nhập trong tháng", "number"),
    "TongTien": ("Tổng tiền", "money"),
    "TrangThaiLo": ("Trạng thái lô", "text"),
    "TrangThaiOrder": ("Trạng thái order", "text"),
    # Aliases the model writes most often (data/eval).
    "DoanhThu": ("Doanh thu", "money"),
    "DoanhThuNgay": ("Doanh thu ngày", "money"),
    "DoanhThuLuyKe": ("Doanh thu luỹ kế", "money"),
    "DoanhThuThangTruoc": ("Doanh thu tháng trước", "money"),
    "TongThu": ("Tổng thu", "money"),
    "TongGiaTri": ("Tổng giá trị", "money"),
    "GiaTriHuy": ("Giá trị hủy", "money"),
    "TrungBinhMoiHoaDon": ("Trung bình mỗi hoá đơn", "money"),
    "TrungBinhHoaDon": ("Trung bình hoá đơn", "money"),
    "TrungBinhMoiNgay": ("Trung bình mỗi ngày", "money"),
    "BienLoiNhuan": ("Biên lợi nhuận", "percent"),
    "PhanTramThayDoi": ("Thay đổi (%)", "percent"),
    "TiLePhanTram": ("Tỉ lệ (%)", "percent"),
    "SoDon": ("Số đơn", "number"),
    "SoDonHuy": ("Số đơn hủy", "number"),
    "SoDonMangVe": ("Số đơn mang về", "number"),
    "SoDonDangMo": ("Số đơn đang mở", "number"),
    "SoHoaDon": ("Số hoá đơn", "number"),
    "SoGiaoDich": ("Số giao dịch", "number"),
    "SoGiaoDichTienMat": ("Giao dịch tiền mặt", "number"),
    "SoGiaoDichQR": ("Giao dịch QR", "number"),
    "SoLuongBan": ("Số lượng bán", "number"),
    "SoLuongTieuHao": ("Số lượng tiêu hao", "number"),
    "SoNguyenLieu": ("Số nguyên liệu", "number"),
    "SoNguyenLieuHet": ("Nguyên liệu đã hết", "number"),
    "SoNguyenLieuCanhBao": ("Nguyên liệu cảnh báo", "number"),
    "TongNhap": ("Tổng nhập", "number"),
    "TongXuat": ("Tổng xuất", "number"),
    "TongTon": ("Tổng tồn", "number"),
    "TongTieuHao": ("Tổng tiêu hao", "number"),
    "Gio": ("Giờ", "text"),
    "SoBan": ("Số bàn", "number"),
    "SoNgay": ("Số ngày", "number"),
}

_MONEY = ("tien", "gia", "doanhthu", "loinhuan", "chiphi", "giavon", "thu")
_PERCENT = ("tyle", "tile", "phantram", "tytrong", "percent")
_DATETIME = ("thoidiem",)
_DATE = ("ngay", "date", "hansudung")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        Decimal(str(value))
    except InvalidOperation:
        return False
    return True


def _guess(column: str, rows: list[dict[str, Any]]) -> Kind:
    name = column.lower()
    values = [row.get(column) for row in rows if row.get(column) is not None]
    numeric = bool(values) and all(_is_number(v) for v in values)
    if any(h in name for h in _PERCENT) and numeric:
        return "percent"
    if any(h in name for h in _DATETIME):
        return "datetime"
    if any(h in name for h in _DATE):
        return "date"
    if numeric and any(h in name for h in _MONEY):
        return "money"
    return "number" if numeric else "text"


def describe_columns(columns: list[str], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for column in columns:
        label, kind = KNOWN.get(column, (_CAMEL.sub(" ", column), _guess(column, rows)))
        out.append({"key": column, "label": label, "kind": kind})
    return out
