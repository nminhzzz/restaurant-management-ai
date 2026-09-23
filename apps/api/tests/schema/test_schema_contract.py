import app.modules.ai.models
import app.modules.catalog.models
import app.modules.inventory.models
import app.modules.sales.models
import app.modules.settings.models
import app.shared.audit  # noqa: F401
from app.shared.base import Base

EXPECTED_TABLES = {
    "VAI_TRO",
    "NGUOI_DUNG",
    "CAU_HINH_HE_THONG",
    "NHAT_KY_HE_THONG",
    "NHOM_MON",
    "MON_AN",
    "LICH_SU_GIA_MON",
    "CONG_THUC",
    "CHI_TIET_CONG_THUC",
    "NGUYEN_LIEU",
    "NHA_CUNG_CAP",
    "BAN",
    "ORDER",
    "CHI_TIET_ORDER",
    "LICH_SU_DOI_BAN",
    "HOA_DON",
    "GIAO_DICH_THANH_TOAN",
    "PHIEU_BEP",
    "PHIEU_NHAP_KHO",
    "CHI_TIET_PHIEU_NHAP",
    "LO_NGUYEN_LIEU",
    "PHIEU_XUAT_KHO",
    "CHI_TIET_PHIEU_XUAT",
    "PHIEU_KIEM_KE",
    "CHI_TIET_KIEM_KE",
    "GIAO_DICH_KHO",
    "GIA_BINH_QUAN_THANG",
    "PHIEN_CHAT_AI",
    "TRUY_VAN_AI",
}

EXPECTED_INDEXES = {
    ("ORDER", ("BusinessDate", "MaBan")),
    ("CHI_TIET_ORDER", ("MaMon", "MaOrder")),
    ("GIAO_DICH_KHO", ("MaNguyenLieu", "ThoiDiem")),
    ("LO_NGUYEN_LIEU", ("MaNguyenLieu", "TrangThai", "NgayNhap")),
    ("GIAO_DICH_THANH_TOAN", ("MaOrder", "TrangThai")),
    ("NGUOI_DUNG", ("MaVaiTro",)),
    ("NHAT_KY_HE_THONG", ("ThoiDiem",)),
    ("HOA_DON", ("ThoiDiemXuat",)),
    ("TRUY_VAN_AI", ("MaPhien", "ThoiDiem")),
}


def test_the_schema_has_exactly_the_29_tables_of_the_report() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_the_index_strategy_of_section_3_2_3_is_present() -> None:
    for table, columns in EXPECTED_INDEXES:
        indexes = Base.metadata.tables[table].indexes
        assert any(tuple(c.name for c in index.columns) == columns for index in indexes), table
