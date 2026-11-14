"""Human labels and value kinds for the assistant's result columns.

Column names come from the `vw_ai_*` views or from aliases the model writes. Known
names get a Vietnamese label; anything else is split on CamelCase, each syllable gets its
accents back from a domain dictionary, and the column is typed from its name, then from
its values.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

Kind = Literal["text", "money", "number", "date", "datetime", "percent"]

KNOWN: dict[str, tuple[str, Kind]] = {
    "BusinessDate": ("Ngày kinh doanh", "date"),
    "CanhBaoTonThap": ("Cảnh báo tồn thấp", "number"),
    "DonGiaBinhQuan": ("Đơn giá bình quân", "money"),
    "DonGiaMon": ("Đơn giá món", "money"),
    "DonGiaNhap": ("Đơn giá nhập", "money"),
    "DonViTinh": ("Đơn vị tính", "text"),
    "GiaTri": ("Giá trị", "money"),
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
    "SoLuongGiu": ("Số lượng đang giữ", "number"),
    "SoLuongKhaDung": ("Số lượng khả dụng", "number"),
    "SoTien": ("Số tiền", "money"),
    "TenMon": ("Tên món", "text"),
    "TenNguyenLieu": ("Tên nguyên liệu", "text"),
    "TenNhaCungCap": ("Nhà cung cấp", "text"),
    "TenNhom": ("Nhóm món", "text"),
    "Thang": ("Tháng", "text"),
    "ThanhTienMon": ("Thành tiền", "money"),
    "ThoiDiemHieuLuc": ("Thời điểm hiệu lực", "datetime"),
    "ThoiDiemXuat": ("Thời điểm xuất", "datetime"),
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
    "LoiNhuanGop": ("Lợi nhuận gộp", "money"),
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
    "SoGiaoDichKho": ("Số giao dịch kho", "number"),
}

_MONEY = ("tien", "gia", "doanhthu", "loinhuan", "chiphi", "giavon", "thu")
_PERCENT = ("tyle", "tile", "phantram", "tytrong", "percent")
_DATETIME = ("thoidiem",)
_DATE = ("ngay", "date", "hansudung")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")

# Unaccented syllables of the restaurant's column aliases. A syllable with two readings
# in this domain is resolved by its neighbour in `_accent`; anything unknown is kept.
_SYLLABLES = {
    "ban": "bán",
    "bao": "báo",
    "bien": "biên",
    "binh": "bình",
    "canh": "cảnh",
    "cao": "cao",
    "cap": "cấp",
    "chenh": "chênh",
    "chi": "chi",
    "cho": "chờ",
    "chua": "chưa",
    "con": "còn",
    "cuoi": "cuối",
    "cung": "cung",
    "dang": "đang",
    "dau": "đầu",
    "dich": "dịch",
    "diem": "điểm",
    "doanh": "doanh",
    "doi": "đổi",
    "don": "đơn",
    "dong": "dòng",
    "dung": "dụng",
    "gia": "giá",
    "gian": "gian",
    "giam": "giảm",
    "giao": "giao",
    "gio": "giờ",
    "giu": "giữ",
    "gop": "gộp",
    "han": "hạn",
    "hang": "hàng",
    "hao": "hao",
    "het": "hết",
    "hien": "hiện",
    "hoa": "hoá",
    "hom": "hôm",
    "huy": "hủy",
    "kha": "khả",
    "khach": "khách",
    "kho": "kho",
    "ke": "kế",
    "ky": "kỳ",
    "lai": "lại",
    "lan": "lần",
    "le": "lệ",
    "lech": "lệch",
    "lieu": "liệu",
    "lo": "lô",
    "loai": "loại",
    "loi": "lợi",
    "luong": "lượng",
    "luot": "lượt",
    "luy": "luỹ",
    "ma": "mã",
    "mang": "mang",
    "mat": "mặt",
    "mo": "mở",
    "moi": "mới",
    "mon": "món",
    "muc": "mức",
    "nam": "năm",
    "nay": "nay",
    "ngay": "ngày",
    "nguoi": "người",
    "nguyen": "nguyên",
    "nha": "nhà",
    "nhap": "nhập",
    "nhat": "nhất",
    "nhom": "nhóm",
    "nhuan": "nhuận",
    "phan": "phần",
    "phi": "phí",
    "phieu": "phiếu",
    "phuc": "phục",
    "phuong": "phương",
    "phut": "phút",
    "qua": "qua",
    "quan": "quân",
    "ra": "ra",
    "sau": "sau",
    "so": "số",
    "su": "sử",
    "tai": "tại",
    "tang": "tăng",
    "te": "tế",
    "ten": "tên",
    "theo": "theo",
    "thai": "thái",
    "thang": "tháng",
    "thanh": "thành",
    "thap": "thấp",
    "thay": "thay",
    "thieu": "thiểu",
    "thoi": "thời",
    "thu": "thu",
    "thuc": "thực",
    "ti": "tỉ",
    "tien": "tiền",
    "tieu": "tiêu",
    "toan": "toán",
    "toi": "tối",
    "ton": "tồn",
    "tong": "tổng",
    "tram": "trăm",
    "trang": "trạng",
    "tri": "trị",
    "trong": "trong",
    "truoc": "trước",
    "trung": "trung",
    "tu": "từ",
    "tuan": "tuần",
    "tung": "từng",
    "ty": "tỷ",
    "vao": "vào",
    "ve": "về",
    "vi": "vị",
    "von": "vốn",
    "vu": "vụ",
    "xuat": "xuất",
}
_WEEKDAY_AFTER_THU = {"trong", "hai", "ba", "tu", "nam", "sau", "bay"}


def _accent(column: str) -> str:
    """'TongSoDonMoi' -> 'Tổng số đơn mới'; unknown syllables are kept as written."""
    tokens = _CAMEL.sub(" ", column).split()
    lower = [token.lower() for token in tokens]
    words = []
    for i, token in enumerate(lower):
        before = lower[i - 1] if i else ""
        after = lower[i + 1] if i + 1 < len(lower) else ""
        word = _SYLLABLES.get(token)
        if token == "ban" and before in ("so", "ma"):
            word = "bàn"
        elif token == "thu" and after in _WEEKDAY_AFTER_THU:
            word = "thứ"
        elif token == "tu" and before == "thu":
            word = "tự"
        elif token == "trong" and before in ("ty", "ti"):
            word = "trọng"
        elif token == "doi" and before == "tuong":
            word = "đối"
        elif token == "thanh" and after == "toan":
            word = "thanh"
        elif token == "thuc" and before == "phuong":
            word = "thức"
        elif token == "moi" and after:
            word = "mỗi"
        elif token == "da" and after in ("ban", "thanh", "huy", "nhap", "xuat", "het"):
            word = "đã"
        words.append(word or tokens[i])
    text = " ".join(words)
    return text[:1].upper() + text[1:]


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
    # A numeric column is never a date/datetime — only its non-numeric values can
    # hint at one. "thoigian" (a duration) and "giao" (giao dịch, a transaction)
    # contain "gia" but aren't money.
    if numeric:
        if any(h in name for h in _PERCENT):
            return "percent"
        money_name = name.replace("thoigian", "").replace("giao", "")
        if any(h in money_name for h in _MONEY):
            return "money"
        return "number"
    if any(h in name for h in _DATETIME):
        return "datetime"
    if any(h in name for h in _DATE):
        return "date"
    return "text"


def describe_columns(columns: list[str], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for column in columns:
        label, kind = KNOWN.get(column, (_accent(column), _guess(column, rows)))
        out.append({"key": column, "label": label, "kind": kind})
    return out
