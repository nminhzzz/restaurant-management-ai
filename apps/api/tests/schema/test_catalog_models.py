from app.modules.catalog.models import DiningTable, Dish, RecipeItem


def test_dish_status_is_a_generated_column() -> None:
    column = Dish.__table__.c.TrangThai
    assert column.computed is not None
    assert column.computed.persisted is True


def test_table_active_name_frees_the_name_of_a_soft_deleted_table() -> None:
    column = DiningTable.__table__.c.TenBan_Active
    assert column.computed is not None
    assert "DaXoa" in str(column.computed.sqltext)


def test_recipe_items_carry_no_unit_of_their_own() -> None:
    assert "DonViTinh" not in {c.name for c in RecipeItem.__table__.columns}


def test_recipe_item_primary_key_is_composite() -> None:
    assert {c.name for c in RecipeItem.__table__.primary_key} == {"MaCongThuc", "MaNguyenLieu"}


# --- MON_AN.MaNhomMon is mandatory (report: "đúng một nhóm", appendix D a6) ----------------------


def test_a_dish_must_belong_to_a_group_with_restricting_foreign_key() -> None:
    column = Dish.__table__.c.MaNhomMon
    assert column.nullable is False
    (foreign_key,) = column.foreign_keys
    assert foreign_key.target_fullname == "NHOM_MON.MaNhomMon"
    assert (foreign_key.ondelete, foreign_key.onupdate) == ("RESTRICT", "RESTRICT")


def _load_group_migration():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).parents[2] / "migrations/versions/c3f8a1d7e5b2_require_dish_group.py"
    spec = importlib.util.spec_from_file_location("require_dish_group", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _render(direction: str) -> str:
    import io

    from alembic.migration import MigrationContext
    from alembic.operations import Operations

    migration = _load_group_migration()
    buffer = io.StringIO()
    context = MigrationContext.configure(
        dialect_name="mysql", opts={"as_sql": True, "output_buffer": buffer}
    )
    migration.__dict__["op"] = Operations(context)
    getattr(migration, direction)()
    return buffer.getvalue()


def test_the_group_migration_chains_after_the_current_head_only() -> None:
    migration = _load_group_migration()
    assert migration.down_revision == "a9c4e7d2b6f1"


def test_the_group_migration_adopts_orphan_dishes_before_forbidding_null() -> None:
    sql = _render("upgrade")

    insert = sql.index("INSERT INTO NHOM_MON")
    update = sql.index("UPDATE MON_AN")
    alter = sql.index("MODIFY `MaNhomMon`")
    assert insert < update < alter
    assert "Chưa phân nhóm" in sql
    # The group is only created when a dish lacks one and no live group of that name exists.
    assert "MaNhomMon IS NULL" in sql
    assert "NOT EXISTS" in sql
    assert "BIGINT NOT NULL" in sql[alter : alter + 80]


def test_the_group_migration_downgrade_lets_the_column_be_null_again() -> None:
    sql = _render("downgrade")

    assert "MODIFY `MaNhomMon` BIGINT NULL" in sql
    assert "NOT NULL" not in sql
