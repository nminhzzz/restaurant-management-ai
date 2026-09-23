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
