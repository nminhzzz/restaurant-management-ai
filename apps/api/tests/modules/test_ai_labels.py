import pytest

from app.modules.ai.labels import describe_columns


def _one(column, rows):
    return describe_columns([column], rows)[0]


def test_known_view_columns_get_vietnamese_labels_and_kinds():
    cols = describe_columns(
        ["TenMon", "TongTien", "BusinessDate", "SoLuong"],
        [{"TenMon": "Phở", "TongTien": "65000.0000", "BusinessDate": "2026-09-26", "SoLuong": 2}],
    )
    assert cols == [
        {"key": "TenMon", "label": "Tên món", "kind": "text"},
        {"key": "TongTien", "label": "Tổng tiền", "kind": "money"},
        {"key": "BusinessDate", "label": "Ngày kinh doanh", "kind": "date"},
        {"key": "SoLuong", "label": "Số lượng", "kind": "number"},
    ]


def test_common_aliases_are_known():
    assert _one("DoanhThu", [{"DoanhThu": 1}]) == {
        "key": "DoanhThu",
        "label": "Doanh thu",
        "kind": "money",
    }
    assert _one("SoDon", [{"SoDon": 3}])["label"] == "Số đơn"


def test_unknown_names_are_guessed_from_the_name():
    assert _one("TongTienThang", [{"TongTienThang": 5}])["kind"] == "money"
    assert _one("TyLeHuy", [{"TyLeHuy": 3.5}])["kind"] == "percent"
    assert _one("NgayCuoi", [{"NgayCuoi": "2026-09-01"}])["kind"] == "date"
    assert _one("ThoiDiemMo", [{"ThoiDiemMo": "2026-09-01T10:00:00"}])["kind"] == "datetime"


def test_unknown_numeric_values_are_numbers_and_labels_get_their_accents_back():
    """BA review 14/11/2026: a model alias such as SoDonHang was shown as "So Don Hang"."""
    assert _one("TongSoDonMoi", [{"TongSoDonMoi": 4}]) == {
        "key": "TongSoDonMoi",
        "label": "Tổng số đơn mới",
        "kind": "number",
    }
    assert _one("GhiChuKhac", [{"GhiChuKhac": "x"}])["kind"] == "text"


def test_a_numeric_column_never_becomes_a_date_and_time_hints_win_over_money():
    """Review #7: only non-numeric values may become date/datetime; a name that
    contains a time-duration hint (thoigian) must not be guessed as money even
    though it also contains the money hint 'gia'."""
    assert _one("DoanhThuTheoNgay", [{"DoanhThuTheoNgay": 5000}])["kind"] == "money"
    assert _one("ThoiGianPhucVu", [{"ThoiGianPhucVu": 12}])["kind"] == "number"
    assert _one("NgayCuoi", [{"NgayCuoi": "2026-09-01"}])["kind"] == "date"


def test_a_transaction_count_is_not_money():
    """The "giao" in giao dịch contains the money hint "gia"; 485 transactions are not 485 ₫."""
    assert _one("SoGiaoDichKho", [{"SoGiaoDichKho": 485}])["kind"] == "number"
    assert _one("SoGiaoDich", [{"SoGiaoDich": 12}])["kind"] == "number"
    assert _one("GiaNhapMoi", [{"GiaNhapMoi": 120000}])["kind"] == "money"


@pytest.mark.parametrize(
    ("column", "label"),
    [
        ("SoDonHang", "Số đơn hàng"),
        ("TrungBinhMoiNgay", "Trung bình mỗi ngày"),
        ("SoLuongBan", "Số lượng bán"),
        ("SoBan", "Số bàn"),
        ("ThuTrongTuan", "Thứ trong tuần"),
        ("TyTrongDoanhThu", "Tỷ trọng doanh thu"),
        ("PhuongThucThanhToan", "Phương thức thanh toán"),
        ("SoLuotKhachQR", "Số lượt khách QR"),
        ("XyzAbc", "Xyz Abc"),
    ],
)
def test_ambiguous_syllables_are_read_from_their_neighbours(column, label):
    assert _one(column, [{column: 1}])["label"] == label
