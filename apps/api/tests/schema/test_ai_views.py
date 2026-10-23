"""View column contract + MySQL integration tests for vw_ai_* (C2).

Fast gate (no DB): checks README contract exists.
Integration (mysql): asserts actual view columns == expected on MySQL 8.4.
"""

from pathlib import Path

import pytest
from sqlalchemy import column, false, literal, select, table, text, update

# Expected column sets from db/views/README.md contract (FR-AI-02/03/04).
EXPECTED_COLUMNS = {
    "vw_ai_quanly": {
        "LoaiBanGhi",
        "MaOrder",
        "BusinessDate",
        "LoaiDon",
        "TrangThaiOrder",
        "MaBan",
        "LyDoHuyOrder",
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
        "MaNguyenLieu",
        "TenNguyenLieu",
        "DonViTinh",
        "SoLuongTon",
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
        "SoLuongGiu",
        "SoLuongKhaDung",
    },
    "vw_ai_thungan": {
        "LoaiBanGhi",
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
    },
    "vw_ai_kho": {
        "LoaiBanGhi",
        "MaNguyenLieu",
        "TenNguyenLieu",
        "DonViTinh",
        "SoLuongTon",
        "SoLuongGiu",
        "SoLuongKhaDung",
        "MucTonToiThieu",
        "CanhBaoTonThap",
        "MaGiaoDichKho",
        "BusinessDate",
        "SoLuong",
        "LoaiGiaoDich",
        "MaLo",
        "SoLuongConLai",
        "TrangThaiLo",
        "NgayNhapLo",
        "HanSuDungLo",
    },
}

FORBIDDEN = {"MatKhauHash", "GiaVonUocTinh", "SoDienThoai"}

# FR-AI-03: the cashier must never see cost/purchase-price columns.
FORBIDDEN_CASHIER = {"DonGiaNhap", "GiaBinhQuanThang", "TenNhaCungCap", "MaNguyenLieu"}
# FR-AI-04: the warehouse role must never see revenue/invoice/amount columns.
FORBIDDEN_WAREHOUSE = {"TongTien", "SoTien", "DonGia", "DonGiaMon", "DonGiaNhap"}


def test_view_column_contract_is_documented() -> None:
    readme = (Path(__file__).resolve().parents[4] / "db/views/README.md").read_text(
        encoding="utf-8"
    )
    assert "Hợp đồng cột" in readme
    for view in EXPECTED_COLUMNS:
        assert view in readme


def _view_sql(name: str) -> str:
    return (Path(__file__).resolve().parents[4] / "db" / "views" / f"{name}.sql").read_text(
        encoding="utf-8"
    )


def test_order_line_branches_exclude_cancelled_lines() -> None:
    """A cancelled line never was a sale; the assistant must not count it."""
    for view in ("vw_ai_quanly", "vw_ai_thungan"):
        assert "ct.TrangThai <> 'Đã hủy'" in _view_sql(view), view


def test_payment_branches_only_expose_successful_transactions() -> None:
    """A pending/expired/failed QR is not revenue, and the view has no status column."""
    for view in ("vw_ai_quanly", "vw_ai_thungan"):
        assert "t.TrangThai = 'Thành công'" in _view_sql(view), view


def test_purchase_branch_excludes_cancelled_receipts_and_uses_business_date() -> None:
    sql = _view_sql("vw_ai_quanly")
    assert "pn.TrangThai <> 'Đã hủy'" in sql
    assert "DATE(pn.NgayNhap - INTERVAL 6 HOUR)" in sql


def test_cashier_view_never_carries_cost_or_purchase_price_columns() -> None:
    """FR-AI-03, NFR-06/12: no giá nhập / giá vốn / lợi nhuận theo món."""
    assert EXPECTED_COLUMNS["vw_ai_thungan"].isdisjoint(FORBIDDEN_CASHIER)


def test_warehouse_view_never_carries_revenue_or_amount_columns() -> None:
    """FR-AI-04, NFR-06/12: no doanh thu / hóa đơn / lợi nhuận."""
    assert EXPECTED_COLUMNS["vw_ai_kho"].isdisjoint(FORBIDDEN_WAREHOUSE)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_view_columns_match_contract_on_mysql(mysql_engine_factory, mysql_seed_views) -> None:
    engine = mysql_engine_factory()
    async with engine.connect() as conn:
        for view, expected in EXPECTED_COLUMNS.items():
            result = await conn.execute(
                text(
                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :view"
                ),
                {"view": view},
            )
            cols = {row[0] for row in result.all()}
            assert cols == expected, f"{view}: got {cols}"
            assert cols.isdisjoint(FORBIDDEN), f"{view} leaks forbidden columns"
            if view == "vw_ai_thungan":
                assert cols.isdisjoint(FORBIDDEN_CASHIER), f"{view} leaks cost/purchase columns"
            if view == "vw_ai_kho":
                assert cols.isdisjoint(FORBIDDEN_WAREHOUSE), f"{view} leaks revenue columns"

    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("role", "own_view", "other_view"),
    [
        ("MANAGER", "vw_ai_quanly_order", "vw_ai_kho_ton"),
        ("CASHIER", "vw_ai_thungan_order", "vw_ai_quanly_giavon"),
        ("WAREHOUSE", "vw_ai_kho_ton", "vw_ai_thungan_hoadon"),
    ],
)
async def test_grants_per_role_on_mysql(mysql_engine_factory, role, own_view, other_view) -> None:
    from sqlalchemy.exc import OperationalError

    from app.modules.ai.accounts import readonly_url_for
    from app.shared.roles import Role

    url = readonly_url_for(Role(role))
    if not url:
        pytest.fail(f"AI_READONLY_URL_{role} is required to verify MySQL isolation")
    eng = mysql_engine_factory(url)
    try:
        async with eng.connect() as conn:
            await conn.execute(select(literal(1)).select_from(table(own_view)).limit(1))
            with pytest.raises(OperationalError, match=r"denied|1142"):
                await conn.execute(select(literal(1)).select_from(table(other_view)).limit(1))
            with pytest.raises(OperationalError, match=r"denied|1142"):
                await conn.execute(select(literal(1)).select_from(table("NGUOI_DUNG")).limit(1))
            with pytest.raises(OperationalError, match=r"denied|1142"):
                await conn.execute(
                    update(table("NGUYEN_LIEU", column("SoLuongTon")))
                    .values(SoLuongTon=0)
                    .where(false())
                )
    finally:
        await eng.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_all_topic_views_obey_role_column_restrictions_on_mysql(
    mysql_engine_factory, mysql_seed_views
):
    from app.modules.ai.scope import views_for
    from app.shared.roles import Role

    engine = mysql_engine_factory()
    try:
        async with engine.connect() as conn:
            for role in Role:
                for view in views_for(role):
                    columns = set(
                        (
                            await conn.execute(
                                text(
                                    "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                                    "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=:view"
                                ),
                                {"view": view},
                            )
                        ).scalars()
                    )
                    assert columns, view
                    assert columns.isdisjoint({"MatKhauHash", "SoDienThoai"})
                    if role == Role.CASHIER:
                        assert columns.isdisjoint(FORBIDDEN_CASHIER | {"GiaVonUocTinh", "LoiNhuan"})
                    if role == Role.WAREHOUSE:
                        assert columns.isdisjoint(
                            FORBIDDEN_WAREHOUSE
                            | {"GiaVonUocTinh", "GiaBinhQuanThang", "MaCongThuc", "DinhLuong"}
                        )
                    if view.endswith("_suat"):
                        assert columns == {"MaMon", "TenMon", "SoSuatKhaDung", "ThoiDiemTinh"}
    finally:
        await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_topic_servings_recompute_holds_lots_and_pauses_on_mysql(
    mysql_engine_factory, mysql_seed_views
):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from tests.modules.test_ai_parity import assert_servings_fresh

    engine = mysql_engine_factory()
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            try:
                await assert_servings_fresh(session)
            finally:
                await session.rollback()
    finally:
        await engine.dispose()
