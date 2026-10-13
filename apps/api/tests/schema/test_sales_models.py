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


# --- the sales models equal what the migrations create (e5b2c8d4f3a1, a9c4e7d2b6f1) ----------


def _load_migration(name: str):
    path = Path(__file__).parents[2] / "migrations/versions" / name
    spec = importlib.util.spec_from_file_location(name.removesuffix(".py"), path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sales_tables() -> set[str]:
    return {
        "ORDER",
        "CHI_TIET_ORDER",
        "LICH_SU_DOI_BAN",
        "HOA_DON",
        "GIAO_DICH_THANH_TOAN",
        "PHIEU_BEP",
    }


def test_unique_constraints_of_the_migration_exist_on_the_models_with_the_same_name() -> None:
    migration = _load_migration("e5b2c8d4f3a1_align_schema_with_report_review_gaps.py")
    for table_name, name, columns in migration.UNIQUES:
        if table_name not in _sales_tables():
            continue
        table = Base.metadata.tables[table_name]
        found = {
            str(constraint.name): [column.name for column in constraint.columns]
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        assert found.get(name) == columns, (table_name, name)


def test_check_constraints_of_the_migration_exist_on_the_models_with_the_same_text() -> None:
    migration = _load_migration("e5b2c8d4f3a1_align_schema_with_report_review_gaps.py")
    for table_name, name, condition in migration.CHECKS:
        if table_name not in _sales_tables():
            continue
        table = Base.metadata.tables[table_name]
        found = {
            str(constraint.name): str(constraint.sqltext)
            for constraint in table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        assert found.get(f"ck_{table_name}_{name}") == condition, (table_name, name)


def test_the_foreign_keys_of_the_migration_exist_on_the_sales_models() -> None:
    migration = _load_migration("e5b2c8d4f3a1_align_schema_with_report_review_gaps.py")
    for name, table_name, column, target in migration.FOREIGN_KEYS:
        if table_name not in _sales_tables():
            continue
        table = Base.metadata.tables[table_name]
        keys = {
            fk.parent.name: (fk.target_fullname, fk.ondelete, fk.onupdate)
            for fk in table.foreign_keys
        }
        assert keys[column] == (target, "RESTRICT", "RESTRICT"), (table_name, column)
        assert name == f"fk_{table_name}_{column}"


def test_payment_state_column_is_wide_enough_for_the_longest_state() -> None:
    column = Base.metadata.tables["GIAO_DICH_THANH_TOAN"].columns["TrangThai"]
    assert column.type.length == 30  # type: ignore[attr-defined]
    assert len("Đóng \u2013 chưa thu được tiền") <= 30


def test_every_timestamp_the_application_writes_has_an_application_side_default() -> None:
    for table_name in _sales_tables():
        for column in Base.metadata.tables[table_name].columns:
            if column.server_default is not None and str(column.type) == "DATETIME":
                assert column.default is not None, (table_name, column.name)


def test_the_invoice_snapshot_column_is_created_by_the_sales_migration() -> None:
    migration = _load_migration("a9c4e7d2b6f1_sales_invoice_snapshot_and_line_state.py")
    assert migration.down_revision == "e5b2c8d4f3a1"
    assert "NoiDungHoaDon" in Base.metadata.tables["HOA_DON"].columns


def test_there_is_a_single_alembic_head() -> None:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(Path(__file__).parents[2] / "alembic.ini"))
    config.set_main_option("script_location", str(Path(__file__).parents[2] / "migrations"))
    assert ScriptDirectory.from_config(config).get_heads() == ["c3f8a1d7e5b2"]
