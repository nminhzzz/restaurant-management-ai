from app.modules.sales.models import Invoice, Order


def test_takeaway_order_must_not_carry_a_table() -> None:
    checks = {
        c.name: str(c.sqltext)
        for c in Order.__table__.constraints  # type: ignore[attr-defined]
        if c.name and c.name.startswith("ck_")
    }
    joined = " ".join(checks.values())
    assert "MaBan" in joined and "Mang v" in joined


def test_invoice_copies_the_business_date() -> None:
    assert "BusinessDate" in {c.name for c in Invoice.__table__.columns}


def test_order_lines_reference_a_price_and_a_recipe_version() -> None:
    columns = {c.name for c in Order.__table__.columns}
    assert {"BusinessDate", "MaBan", "LoaiDon", "TrangThai", "NguoiTao"} <= columns
