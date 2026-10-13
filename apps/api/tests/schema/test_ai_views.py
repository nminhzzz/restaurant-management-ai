"""View column contract + MySQL integration tests for vw_ai_* (C2).

Fast gate (no DB): checks README contract exists.
Integration (mysql): asserts actual view columns == expected on MySQL 8.4.
"""

from pathlib import Path

import pytest
import sqlglot
from sqlalchemy import text
from sqlglot import exp

from app.modules.ai.pipeline.prompt import COLUMN_NOTES, VIEW_LOAIBANGHI_VALUES
from app.modules.ai.scope import VIEW_COLUMNS

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
        # FR-SET-03: the Manager inherits the Warehouse scope (held/available stock, lots).
        "SoLuongGiu",
        "SoLuongKhaDung",
        "CanhBaoTonThap",
        "MaLo",
        "SoLuongConLai",
        "TrangThaiLo",
        "NgayNhapLo",
        "HanSuDungLo",
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
EXPECTED_WAREHOUSE_COLUMN_ORDER = [
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
]

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
    assert "`SoLuongGiu`" in readme
    assert "`SoLuongKhaDung`" in readme


def _view_branches(name: str) -> list[exp.Select]:
    path = Path(__file__).resolve().parents[4] / "db/views" / f"{name}.sql"
    branch = sqlglot.parse_one(path.read_text(encoding="utf-8"), read="mysql").expression
    branches: list[exp.Select] = []
    while isinstance(branch, exp.Union):
        assert isinstance(branch.expression, exp.Select)
        branches.append(branch.expression)
        branch = branch.this
    assert isinstance(branch, exp.Select)
    branches.append(branch)
    return branches[::-1]


@pytest.mark.parametrize("view", sorted(EXPECTED_COLUMNS))
def test_scope_columns_match_the_view_ddl(view: str) -> None:
    """The guard's column allow-list (scope.VIEW_COLUMNS) must be the real view columns."""
    branches = _view_branches(view)
    names = [expression.alias_or_name for expression in branches[0].expressions]

    assert len(set(names)) == len(names)
    assert set(names) == EXPECTED_COLUMNS[view]
    assert set(VIEW_COLUMNS[view]) == EXPECTED_COLUMNS[view]
    assert {len(branch.expressions) for branch in branches} == {len(names)}


def test_manager_view_inherits_the_warehouse_scope() -> None:
    """FR-SET-03: every Warehouse column and branch is also readable by the Manager."""
    assert EXPECTED_COLUMNS["vw_ai_kho"] <= EXPECTED_COLUMNS["vw_ai_quanly"]
    branch_names = {
        branch.expressions[0].find(exp.Literal).this for branch in _view_branches("vw_ai_quanly")
    }
    assert {"TON_KHO", "GIAO_DICH_KHO", "LO_NGUYEN_LIEU"} <= branch_names


def test_every_view_branch_is_documented_in_its_header() -> None:
    root = Path(__file__).resolve().parents[4] / "db/views"
    for view in EXPECTED_COLUMNS:
        header = (root / f"{view}.sql").read_text(encoding="utf-8").split("CREATE", 1)[0]
        for branch in _view_branches(view):
            label = branch.expressions[0].find(exp.Literal).this
            assert f"'{label}'" in header, f"{view}: branch {label} missing from header"


@pytest.mark.parametrize("view", sorted(EXPECTED_COLUMNS))
def test_prompt_lists_exactly_the_branches_of_each_view(view: str) -> None:
    branches = tuple(
        branch.expressions[0].find(exp.Literal).this for branch in _view_branches(view)
    )

    assert VIEW_LOAIBANGHI_VALUES[view] == branches


def test_prompt_column_notes_only_describe_real_columns() -> None:
    every_column = set().union(*EXPECTED_COLUMNS.values())

    assert set(COLUMN_NOTES) <= every_column


def test_cashier_view_never_carries_cost_or_purchase_price_columns() -> None:
    """FR-AI-03, NFR-06/12: no giá nhập / giá vốn / lợi nhuận theo món."""
    assert EXPECTED_COLUMNS["vw_ai_thungan"].isdisjoint(FORBIDDEN_CASHIER)


def test_warehouse_view_never_carries_revenue_or_amount_columns() -> None:
    """FR-AI-04, NFR-06/12: no doanh thu / hóa đơn / lợi nhuận."""
    assert EXPECTED_COLUMNS["vw_ai_kho"].isdisjoint(FORBIDDEN_WAREHOUSE)


def test_warehouse_view_union_branches_have_the_same_column_count() -> None:
    view_path = Path(__file__).resolve().parents[4] / "db/views/vw_ai_kho.sql"
    create_view = sqlglot.parse_one(view_path.read_text(encoding="utf-8"), read="mysql")
    branch = create_view.expression
    branches: list[exp.Select] = []
    while isinstance(branch, exp.Union):
        assert isinstance(branch.expression, exp.Select)
        branches.append(branch.expression)
        branch = branch.this
    assert isinstance(branch, exp.Select)
    branches.append(branch)

    assert len(branches) == 3
    assert [len(select.expressions) for select in branches] == [
        len(EXPECTED_COLUMNS["vw_ai_kho"])
    ] * 3
    assert [expression.alias_or_name for expression in branches[-1].expressions] == (
        EXPECTED_WAREHOUSE_COLUMN_ORDER
    )
    for select in branches[:-1]:
        assert all(select.expressions[index].find(exp.Null) is not None for index in (5, 6))


def test_warehouse_view_excludes_expired_holds_and_ineligible_lots() -> None:
    view_sql = (Path(__file__).resolve().parents[4] / "db/views/vw_ai_kho.sql").read_text(
        encoding="utf-8"
    )
    normalized_sql = " ".join(view_sql.lower().split())

    assert "gh.trangthai = 'đang giữ'" in normalized_sql
    assert "gh.thoidiemhethan > current_timestamp" in normalized_sql
    assert "l.soluongconlai > 0" in normalized_sql
    assert "l.trangthai <> 'hết hạn'" in normalized_sql
    assert "date_add(l.hansudung, interval 1 day) > current_timestamp" in normalized_sql


@pytest.mark.integration
@pytest.mark.asyncio
async def test_view_columns_match_contract_on_mysql(mysql_engine_factory) -> None:
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
async def test_warehouse_totals_exclude_expired_holds_and_ineligible_lots(
    mysql_engine_factory,
) -> None:
    engine = mysql_engine_factory()
    async with engine.connect() as conn:
        transaction = await conn.begin()
        try:
            await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            ingredient_result = await conn.execute(
                text(
                    "INSERT INTO NGUYEN_LIEU "
                    "(TenNguyenLieu, DonViTinh, SoLuongTon, Version, DaKhoaDonVi, "
                    "MucTonToiThieu, DaXoa) "
                    "VALUES ('ai-view-hold-contract', 'kg', 60, 1, 0, 1, 0)"
                )
            )
            ingredient_id = ingredient_result.lastrowid

            async def add_lot(quantity: int, status: str, expiry_sql: str) -> int:
                lot_result = await conn.execute(
                    text(
                        "INSERT INTO LO_NGUYEN_LIEU "
                        "(MaNguyenLieu, MaChiTietNhap, SoLuongConLai, TrangThai, NgayNhap, "
                        "LoDieuChinhKiemKe, HanSuDung, SoLuongNhap, DonGia) "
                        f"VALUES (:ingredient, NULL, {quantity}, :status, CURRENT_TIMESTAMP, "
                        f"0, {expiry_sql}, {quantity}, 1)"
                    ),
                    {"ingredient": ingredient_id, "status": status},
                )
                return int(lot_result.lastrowid)

            active_lot_id = await add_lot(10, "Còn hạn", "DATE_ADD(CURRENT_DATE, INTERVAL 5 DAY)")
            status_expired_lot_id = await add_lot(
                20, "Hết hạn", "DATE_ADD(CURRENT_DATE, INTERVAL 5 DAY)"
            )
            date_expired_lot_id = await add_lot(
                30, "Còn hạn", "DATE_SUB(CURRENT_DATE, INTERVAL 1 DAY)"
            )

            async def add_hold(lot_id: int, status: str, expires_sql: str, quantity: int) -> None:
                hold_result = await conn.execute(
                    text(
                        "INSERT INTO GIU_CHO_MON "
                        "(MaLuotChon, MaNguoiDung, MaBan, MaOrder, MaMon, MaCongThuc, "
                        "MaPhienBanGia, SoLuong, GhiChu, ThoiDiemHetHan, TrangThai, "
                        "MaYeuCauGui, MaDongYeuCau, MaChiTietOrder) "
                        f"VALUES ('ai-view-hold-contract', 1, NULL, NULL, 1, 1, 1, {quantity}, "
                        f"NULL, {expires_sql}, :status, NULL, NULL, NULL)"
                    ),
                    {"status": status},
                )
                await conn.execute(
                    text(
                        "INSERT INTO CHI_TIET_GIU_CHO (MaGiuCho, MaLoNguyenLieu, SoLuongGiu) "
                        "VALUES (:hold, :lot, :quantity)"
                    ),
                    {
                        "hold": hold_result.lastrowid,
                        "lot": lot_id,
                        "quantity": quantity,
                    },
                )

            await add_hold(
                active_lot_id, "Đang giữ", "DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 HOUR)", 3
            )
            await add_hold(
                active_lot_id, "Đang giữ", "DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 MINUTE)", 2
            )
            await add_hold(
                active_lot_id, "Đã hủy", "DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 HOUR)", 4
            )
            await add_hold(
                status_expired_lot_id,
                "Đang giữ",
                "DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 HOUR)",
                8,
            )
            await add_hold(
                date_expired_lot_id,
                "Đang giữ",
                "DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 HOUR)",
                9,
            )

            totals = (
                await conn.execute(
                    text(
                        "SELECT SoLuongGiu, SoLuongKhaDung FROM vw_ai_kho "
                        "WHERE LoaiBanGhi = 'TON_KHO' AND MaNguyenLieu = :ingredient"
                    ),
                    {"ingredient": ingredient_id},
                )
            ).one()
            assert tuple(map(float, totals)) == (3.0, 7.0)
        finally:
            await transaction.rollback()
            await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_grants_per_role_on_mysql(mysql_engine_factory) -> None:
    # ai_cashier must not read vw_ai_kho
    from sqlalchemy.exc import OperationalError

    cashier_url = (
        "mysql+asyncmy://ai_cashier:dev-cashier-pass@localhost:3306/restaurant?charset=utf8mb4"
    )
    eng = mysql_engine_factory(cashier_url)
    try:
        async with eng.connect() as conn:
            with pytest.raises(OperationalError, match=r"denied|1142"):
                await conn.execute(text("SELECT COUNT(*) FROM vw_ai_kho"))
    finally:
        await eng.dispose()


@pytest.mark.parametrize("view", ["vw_ai_kho", "vw_ai_quanly"])
def test_effective_min_stock_uses_coalesce_so_zero_is_a_real_threshold(view: str) -> None:
    """NULL means "use the system default"; 0 is a threshold someone chose (FR-INV-07)."""
    view_sql = (Path(__file__).resolve().parents[4] / f"db/views/{view}.sql").read_text(
        encoding="utf-8"
    )
    normalized = " ".join(view_sql.lower().split())

    assert "n.muctontoithieu > 0" not in normalized
    assert normalized.count("coalesce(n.muctontoithieu, (select cfg.nguongtonmacdinh") == 2


@pytest.mark.parametrize("view", ["vw_ai_quanly", "vw_ai_thungan", "vw_ai_kho"])
def test_every_char_cast_in_a_view_pins_its_collation(view: str) -> None:
    """A bare CAST(.. AS CHAR) takes the session collation and breaks the UNION at query time."""
    import re

    sql = (Path(__file__).resolve().parents[4] / f"db/views/{view}.sql").read_text(encoding="utf-8")
    casts = re.findall(r"AS CHAR\(\d+\)\)(?! COLLATE utf8mb4_unicode_ci)", sql)

    assert casts == [], f"{view}: {len(casts)} CAST(.. AS CHAR) without COLLATE utf8mb4_unicode_ci"
