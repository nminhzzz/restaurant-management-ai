from app.modules.settings.models import User
from app.shared.base import NAMING_CONVENTION, Base

EXPECTED = {
    "VAI_TRO": {"MaVaiTro", "TenVaiTro", "MoTa"},
    "NGUOI_DUNG": {
        "MaNguoiDung",
        "TenDangNhap",
        "MatKhauHash",
        "HoTen",
        "SoDienThoai",
        "MaVaiTro",
        "TrangThai",
        "NgayTao",
    },
    "CAU_HINH_HE_THONG": {
        "MaCauHinh",
        "TenNhaHang",
        "DiaChi",
        "MauHoaDon",
        "NguongTonMacDinh",
        "GioBatDauBusinessDate",
    },
}


def test_table_and_column_names_follow_the_report() -> None:
    for table, columns in EXPECTED.items():
        assert table in Base.metadata.tables
        assert {c.name for c in Base.metadata.tables[table].columns} == columns


def test_user_is_restricted_by_role() -> None:
    fk = next(iter(User.__table__.foreign_keys))
    assert fk.target_fullname == "VAI_TRO.MaVaiTro"
    assert fk.ondelete == "RESTRICT"


def test_check_constraints_get_a_name_from_the_convention() -> None:
    assert "ck" in NAMING_CONVENTION
    assert NAMING_CONVENTION["ck"].startswith("ck_")
