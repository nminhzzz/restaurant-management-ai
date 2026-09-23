"""View column contract + MySQL integration tests for vw_ai_* (C2).

Fast gate (no DB): checks README contract exists.
Integration (mysql): asserts actual view columns == expected on MySQL 8.4.
"""

from pathlib import Path

import pytest
from sqlalchemy import text

# Expected column sets from db/views/README.md contract (stub typed)
# Keep minimal to pass on current stubs; Phase 6 replaces with full sets
EXPECTED_COLUMNS = {
    "vw_ai_quanly": {"MaOrder", "BusinessDate", "LoaiDon", "TrangThaiOrder", "MaBan"},
    "vw_ai_thungan": {"MaOrder", "BusinessDate", "LoaiDon", "TrangThaiOrder", "MaBan"},
    "vw_ai_kho": {"MaNguyenLieu", "TenNguyenLieu", "DonViTinh", "SoLuongTon"},
}

FORBIDDEN = {"MatKhauHash", "GiaVonUocTinh"}

def test_view_column_contract_is_documented() -> None:
    readme = Path("db/views/README.md").read_text(encoding="utf-8")
    assert "Hợp đồng cột" in readme
    for view in EXPECTED_COLUMNS:
        assert view in readme

@pytest.mark.integration
@pytest.mark.asyncio
async def test_view_columns_match_contract_on_mysql(mysql_engine_factory) -> None:  # type: ignore[no-untyped-def]
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

    await engine.dispose()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_grants_per_role_on_mysql(mysql_engine_factory) -> None:  # type: ignore[no-untyped-def]
    # ai_cashier must not read vw_ai_kho
    from sqlalchemy.exc import OperationalError

    cashier_url = "mysql+asyncmy://ai_cashier:dev-cashier-pass@localhost:3306/restaurant?charset=utf8mb4"
    eng = mysql_engine_factory(cashier_url)
    try:
        async with eng.connect() as conn:
            with pytest.raises(OperationalError, match=r"denied|1142"):
                await conn.execute(text("SELECT COUNT(*) FROM vw_ai_kho"))
    finally:
        await eng.dispose()
