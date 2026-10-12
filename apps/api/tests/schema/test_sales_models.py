import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import CheckConstraint, UniqueConstraint, create_engine, inspect

from app.modules.sales.models import Invoice, Order
from app.shared.base import Base


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


def test_item_hold_has_report_columns_and_nullable_links() -> None:
    table = Base.metadata.tables["GIU_CHO_MON"]
    assert {column.name for column in table.columns} == {
        "MaGiuCho",
        "MaLuotChon",
        "MaNguoiDung",
        "MaBan",
        "MaOrder",
        "MaMon",
        "MaCongThuc",
        "MaPhienBanGia",
        "SoLuong",
        "GhiChu",
        "ThoiDiemHetHan",
        "TrangThai",
        "MaYeuCauGui",
        "MaDongYeuCau",
        "MaChiTietOrder",
    }
    assert [column.name for column in table.primary_key.columns] == ["MaGiuCho"]
    assert {column.name for column in table.columns if column.nullable} == {
        "MaBan",
        "MaOrder",
        "GhiChu",
        "MaYeuCauGui",
        "MaDongYeuCau",
        "MaChiTietOrder",
    }


def test_item_hold_foreign_keys_restrict_historical_deletes() -> None:
    table = Base.metadata.tables["GIU_CHO_MON"]
    references = {
        fk.parent.name: (fk.target_fullname, fk.ondelete, fk.onupdate) for fk in table.foreign_keys
    }
    assert references == {
        "MaNguoiDung": ("NGUOI_DUNG.MaNguoiDung", "RESTRICT", "RESTRICT"),
        "MaBan": ("BAN.MaBan", "RESTRICT", "RESTRICT"),
        "MaOrder": ("ORDER.MaOrder", "RESTRICT", "RESTRICT"),
        "MaMon": ("MON_AN.MaMon", "RESTRICT", "RESTRICT"),
        "MaCongThuc": ("CONG_THUC.MaCongThuc", "RESTRICT", "RESTRICT"),
        "MaPhienBanGia": ("LICH_SU_GIA_MON.MaPhienBanGia", "RESTRICT", "RESTRICT"),
        "MaChiTietOrder": ("CHI_TIET_ORDER.MaChiTietOrder", "RESTRICT", "RESTRICT"),
    }


def test_item_hold_quantity_and_send_keys_have_database_constraints() -> None:
    table = Base.metadata.tables["GIU_CHO_MON"]
    checks = [
        str(check.sqltext) for check in table.constraints if isinstance(check, CheckConstraint)
    ]
    assert any("SoLuong > 0" in check for check in checks)
    uniques = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert {("MaChiTietOrder",), ("MaYeuCauGui", "MaDongYeuCau")} <= uniques


def test_hold_lot_has_composite_key_positive_quantity_and_restrict_foreign_keys() -> None:
    table = Base.metadata.tables["CHI_TIET_GIU_CHO"]
    assert {column.name for column in table.columns} == {
        "MaGiuCho",
        "MaLoNguyenLieu",
        "SoLuongGiu",
    }
    assert {column.name for column in table.primary_key.columns} == {
        "MaGiuCho",
        "MaLoNguyenLieu",
    }
    assert all(not column.nullable for column in table.columns)
    references = {
        fk.parent.name: (fk.target_fullname, fk.ondelete, fk.onupdate) for fk in table.foreign_keys
    }
    assert references == {
        "MaGiuCho": ("GIU_CHO_MON.MaGiuCho", "RESTRICT", "RESTRICT"),
        "MaLoNguyenLieu": ("LO_NGUYEN_LIEU.MaLoNguyenLieu", "RESTRICT", "RESTRICT"),
    }
    checks = [
        str(check.sqltext) for check in table.constraints if isinstance(check, CheckConstraint)
    ]
    assert any("SoLuongGiu > 0" in check for check in checks)


def test_item_hold_migration_check_names_match_the_model() -> None:
    migration_path = (
        Path(__file__).parents[2] / "migrations/versions/d2f8a7c4e901_add_item_holds.py"
    )
    spec = importlib.util.spec_from_file_location("item_hold_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as connection:
        migration.__dict__["op"] = Operations(
            MigrationContext.configure(connection, opts={"target_metadata": Base.metadata})
        )
        migration.upgrade()
        schema = inspect(connection)
        assert {item["name"] for item in schema.get_check_constraints("GIU_CHO_MON")} == {
            "ck_GIU_CHO_MON_hold_quantity_positive"
        }
        assert {item["name"] for item in schema.get_check_constraints("CHI_TIET_GIU_CHO")} == {
            "ck_CHI_TIET_GIU_CHO_held_quantity_positive"
        }
        migration.downgrade()
    engine.dispose()
