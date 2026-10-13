"""Role → database view mapping (NFR-06, NFR-12).

The assistant never touches the core business tables. Each role gets one
read-only view, granted to a dedicated read-only database account, and the
generator is only ever told about that single view. The columns each view exposes are
listed here too, so the SQL guard can check column references (report §5.1.1);
`tests/schema/test_ai_views.py` fails if this list drifts from `db/views/*.sql`.
"""

from types import MappingProxyType

from app.shared.roles import Role

ROLE_VIEWS: MappingProxyType[Role, str] = MappingProxyType(
    {
        Role.MANAGER: "vw_ai_quanly",
        Role.CASHIER: "vw_ai_thungan",
        Role.WAREHOUSE: "vw_ai_kho",
    }
)


def views_for(role: Role) -> frozenset[str]:
    """The set of views the assistant may read for this role."""
    return frozenset({ROLE_VIEWS[role]})


_COMMON_STOCK = (
    "MaNguyenLieu",
    "TenNguyenLieu",
    "DonViTinh",
    "SoLuongTon",
)
_STOCK_AVAILABILITY = ("SoLuongGiu", "SoLuongKhaDung", "CanhBaoTonThap")
_LOT = ("MaLo", "SoLuongConLai", "TrangThaiLo", "NgayNhapLo", "HanSuDungLo")
_SALES = (
    "MaOrder",
    "BusinessDate",
    "LoaiDon",
    "TrangThaiOrder",
    "MaBan",
    "MaHoaDon",
    "ThoiDiemXuat",
    "TongTien",
    "MaGiaoDich",
    "PhuongThuc",
    "SoTien",
    "TenMon",
    "TenNhom",
    "SoLuongMon",
    "DonGiaMon",
    "ThanhTienMon",
)

VIEW_COLUMNS: MappingProxyType[str, frozenset[str]] = MappingProxyType(
    {
        "vw_ai_thungan": frozenset({"LoaiBanGhi", *_SALES}),
        "vw_ai_kho": frozenset(
            {
                "LoaiBanGhi",
                *_COMMON_STOCK,
                *_STOCK_AVAILABILITY,
                "MucTonToiThieu",
                "MaGiaoDichKho",
                "BusinessDate",
                "SoLuong",
                "LoaiGiaoDich",
                *_LOT,
            }
        ),
        "vw_ai_quanly": frozenset(
            {
                "LoaiBanGhi",
                *_SALES,
                "LyDoHuyOrder",
                *_COMMON_STOCK,
                *_STOCK_AVAILABILITY,
                "MucTonToiThieu",
                "Thang",
                "GiaBinhQuanThang",
                "TongSoLuongNhapThang",
                "MaGiaoDichKho",
                "SoLuong",
                "LoaiGiaoDich",
                "MaPhieuNhap",
                "TenNhaCungCap",
                "DonGiaNhap",
                "SoLuongNhap",
                *_LOT,
            }
        ),
    }
)


def columns_for(role: Role) -> frozenset[str]:
    """The columns of the one view this role may read."""
    return VIEW_COLUMNS[ROLE_VIEWS[role]]


def foreign_columns_for(role: Role) -> frozenset[str]:
    """Columns that exist only in other roles' views (asking for them is out of scope)."""
    others = frozenset().union(
        *(cols for view, cols in VIEW_COLUMNS.items() if view != ROLE_VIEWS[role])
    )
    return others - columns_for(role)
