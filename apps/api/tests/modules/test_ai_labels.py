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


def test_unknown_numeric_values_are_numbers_and_labels_split_camel_case():
    assert _one("TongSoDonMoi", [{"TongSoDonMoi": 4}]) == {
        "key": "TongSoDonMoi",
        "label": "Tong So Don Moi",
        "kind": "number",
    }
    assert _one("GhiChuKhac", [{"GhiChuKhac": "x"}])["kind"] == "text"
