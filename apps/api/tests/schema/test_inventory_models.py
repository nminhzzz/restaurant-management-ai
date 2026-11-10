from app.modules.inventory.models import (
    AverageCostHistory,
    IngredientLot,
    StockMovement,
    StocktakeLine,
)


def test_stocktake_difference_is_generated() -> None:
    column = StocktakeLine.__table__.c.ChenhLech
    assert column.computed is not None
    assert "TonThucTe" in str(column.computed.sqltext)


def test_movement_must_name_the_source_document_matching_its_kind() -> None:
    checks = [
        str(c.sqltext)
        for c in StockMovement.__table__.constraints  # type: ignore[attr-defined]
        if c.name and c.name.startswith("ck_")
    ]
    joined = " ".join(checks)
    for column in ("MaChiTietNhap", "MaChiTietOrder", "MaChiTietXuat", "MaChiTietKiemKe"):
        assert column in joined


def test_every_movement_carries_the_business_date() -> None:
    assert "BusinessDate" in {c.name for c in StockMovement.__table__.columns}


def test_lot_can_be_flagged_as_a_stocktake_adjustment() -> None:
    assert "LoDieuChinhKiemKe" in {c.name for c in IngredientLot.__table__.columns}


def test_one_lot_per_receipt_line() -> None:
    assert IngredientLot.__table__.c.MaChiTietNhap.unique is True


def test_cost_history_is_keyed_by_ingredient_and_effective_time() -> None:
    """Document 04 F.27."""
    table = AverageCostHistory.__table__
    assert {c.name for c in table.primary_key} == {"MaNguyenLieu", "ThoiDiemHieuLuc"}
    assert table.c.DonGiaBinhQuan.nullable is False
    assert table.c.SoLuongTon.nullable is False
    assert table.c.MaGiaoDichKho.nullable is True


def test_a_movement_value_may_be_unknown_but_is_never_defaulted() -> None:
    column = StockMovement.__table__.c.GiaTri
    assert column.nullable is True
    assert column.default is None and column.server_default is None
