"""Catalogue rules of the report: Tables 9/10, FR-CAT-03/05/09/17-27, FR-SET-08/09."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.modules.catalog.models import (
    DiningTable,
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
)
from app.modules.catalog.versions import (
    active_price_version,
    active_recipe,
    promote_due_versions,
)
from app.modules.sales.models import ItemHold, Order
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from tests.helpers import FIXED_NOW

CATALOG = "/api/v1/catalog"
TODAY = date(2026, 9, 24)  # FIXED_NOW falls on this Business Date


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _audit(session, action: str) -> list[SystemAuditLog]:
    return list(
        (
            await session.execute(
                select(SystemAuditLog)
                .where(SystemAuditLog.action == action)
                .order_by(SystemAuditLog.id)
            )
        )
        .scalars()
        .all()
    )


# --- Tables 9 and 10: who may read the catalogue ----------------------------------------------


@pytest.mark.parametrize(
    ("path", "allowed", "denied"),
    [
        ("/groups", ("manager", "cashier"), ("warehouse",)),
        ("/dishes", ("manager", "cashier"), ("warehouse",)),
        ("/tables", ("manager", "cashier"), ("warehouse",)),
        ("/ingredients", ("manager", "warehouse"), ("cashier",)),
        ("/suppliers", ("manager", "warehouse"), ("cashier",)),
    ],
)
async def test_catalogue_reads_follow_the_permission_matrix(
    api_client, manager_token, cashier_token, warehouse_token, path, allowed, denied
):
    tokens = {"manager": manager_token, "cashier": cashier_token, "warehouse": warehouse_token}
    async with api_client as client:
        anonymous = await client.get(f"{CATALOG}{path}")
        statuses = {
            role: (await client.get(f"{CATALOG}{path}", headers=_auth(token))).status_code
            for role, token in tokens.items()
        }

    assert anonymous.status_code == 401
    assert all(statuses[role] == 200 for role in allowed), statuses
    assert all(statuses[role] == 403 for role in denied), statuses


async def test_a_supplier_detail_is_not_open_to_the_cashier(
    api_client, manager_token, cashier_token
):
    async with api_client as client:
        created = await client.post(
            f"{CATALOG}/suppliers",
            json={
                "TenNhaCungCap": "Chợ đầu mối",
                "SoDienThoai": "0909",
                "NguoiLienHe": "Cô Lan",
                "Email": "lan@example.com",
                "DiaChi": "Hà Nội",
            },
            headers=_auth(manager_token),
        )
        sid = created.json()["MaNhaCungCap"]
        as_cashier = await client.get(f"{CATALOG}/suppliers/{sid}", headers=_auth(cashier_token))
        as_manager = await client.get(f"{CATALOG}/suppliers/{sid}", headers=_auth(manager_token))
        missing = await client.get(f"{CATALOG}/suppliers/999", headers=_auth(manager_token))

    assert as_cashier.status_code == 403
    assert as_manager.json()["NguoiLienHe"] == "Cô Lan"
    assert as_manager.json()["Email"] == "lan@example.com"
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"


# --- groups and dishes ------------------------------------------------------------------------


async def test_a_dish_must_name_exactly_one_live_group(api_client, manager_token, session):
    group = DishGroup(name="Đã xóa", display_order=1, is_deleted=True)
    session.add(group)
    await session.commit()
    async with api_client as client:
        no_group = await client.post(
            f"{CATALOG}/dishes", json={"TenMon": "Phở"}, headers=_auth(manager_token)
        )
        deleted_group = await client.post(
            f"{CATALOG}/dishes",
            json={"TenMon": "Phở", "MaNhomMon": group.id},
            headers=_auth(manager_token),
        )

    assert no_group.status_code == 422
    assert deleted_group.status_code == 422
    assert (await session.execute(select(Dish))).first() is None


async def test_a_group_that_never_held_a_dish_is_removed_for_good(
    api_client, manager_token, session
):
    async with api_client as client:
        created = await client.post(
            f"{CATALOG}/groups", json={"TenNhom": "Tráng miệng"}, headers=_auth(manager_token)
        )
        gid = created.json()["MaNhomMon"]
        deleted = await client.delete(f"{CATALOG}/groups/{gid}", headers=_auth(manager_token))

    assert deleted.status_code == 204
    assert await session.get(DishGroup, gid) is None
    entry = (await _audit(session, "DELETE_GROUP"))[0]
    assert entry.before["TenNhomMon"] == "Tráng miệng"
    assert entry.after is None


async def test_a_group_that_held_a_dish_is_only_soft_deleted(
    api_client, manager_token, session, group_with_dish
):
    async with api_client as client:
        await client.delete(
            f"{CATALOG}/dishes/{group_with_dish.dish_id}", headers=_auth(manager_token)
        )
        deleted = await client.delete(
            f"{CATALOG}/groups/{group_with_dish.id}", headers=_auth(manager_token)
        )

    assert deleted.status_code == 204
    row = await session.get(DishGroup, group_with_dish.id)
    assert row is not None and row.is_deleted is True and row.deleted_at is not None
    entry = (await _audit(session, "DELETE_GROUP"))[0]
    assert entry.before["DaXoa"] is False
    assert entry.after["DaXoa"] is True


async def test_dish_updates_carry_before_and_after(api_client, manager_token, session, dish):
    async with api_client as client:
        await client.patch(
            f"{CATALOG}/dishes/{dish.id}", json={"TenMon": "Món mới"}, headers=_auth(manager_token)
        )

    entry = (await _audit(session, "UPDATE_DISH"))[0]
    assert entry.before["TenMon"] != "Món mới"
    assert entry.after["TenMon"] == "Món mới"


# --- pending versions: overwrite and cancel leave a trace (FR-CAT-05/09/10/21/22) --------------


async def test_overwriting_a_pending_price_cancels_the_old_one_and_audits_it(
    api_client, manager_token, session, dish
):
    dish_id = dish.id
    async with api_client as client:
        first = await client.post(
            f"{CATALOG}/dishes/{dish_id}/prices/schedule",
            json={"Gia": "50000"},
            headers=_auth(manager_token),
        )
        second = await client.post(
            f"{CATALOG}/dishes/{dish_id}/prices/schedule",
            json={"Gia": "55000"},
            headers=_auth(manager_token),
        )

    assert first.status_code == second.status_code == 201
    rows = {
        row.id: row
        for row in (
            await session.execute(
                select(DishPriceVersion).where(DishPriceVersion.dish_id == dish_id)
            )
        ).scalars()
    }
    assert rows[first.json()["MaLichSuGia"]].status == "Đã hủy"
    assert rows[second.json()["MaLichSuGia"]].status == "Chờ áp dụng"
    cancelled = (await _audit(session, "CANCEL_PRICE_CHANGE"))[0]
    assert cancelled.target_id == str(first.json()["MaLichSuGia"])
    assert cancelled.before["TrangThai"] == "Chờ áp dụng"
    assert cancelled.after["TrangThai"] == "Đã hủy"
    assert "ghi đè" in cancelled.reason
    assert cancelled.user_id is not None


async def test_cancelling_a_pending_price_keeps_the_row_as_cancelled(
    api_client, manager_token, session, dish
):
    async with api_client as client:
        pending = await client.post(
            f"{CATALOG}/dishes/{dish.id}/prices/schedule",
            json={"Gia": "50000"},
            headers=_auth(manager_token),
        )
        vid = pending.json()["MaLichSuGia"]
        cancelled = await client.delete(f"{CATALOG}/prices/{vid}", headers=_auth(manager_token))
        again = await client.delete(f"{CATALOG}/prices/{vid}", headers=_auth(manager_token))

    assert cancelled.status_code == 204
    assert again.status_code == 404
    assert (await session.get(DishPriceVersion, vid)).status == "Đã hủy"
    entry = (await _audit(session, "CANCEL_PRICE_CHANGE"))[0]
    assert entry.before["GiaBan"] == 50000


async def test_overwriting_a_pending_recipe_keeps_the_old_lines_and_audits_it(
    api_client, manager_token, session, dish_with_recipe, flour
):
    dish_id = dish_with_recipe.id
    body = {"items": [{"MaNguyenLieu": flour.id, "SoLuong": "0.5"}]}
    async with api_client as client:
        first = await client.post(
            f"{CATALOG}/dishes/{dish_id}/recipes/schedule", json=body, headers=_auth(manager_token)
        )
        second = await client.post(
            f"{CATALOG}/dishes/{dish_id}/recipes/schedule",
            json={"items": [{"MaNguyenLieu": flour.id, "SoLuong": "0.9"}]},
            headers=_auth(manager_token),
        )

    first_id = first.json()["MaCongThuc"]
    assert second.status_code == 201
    assert (await session.get(Recipe, first_id)).status == "Đã hủy"
    kept = (
        await session.execute(select(RecipeItem).where(RecipeItem.recipe_id == first_id))
    ).scalar_one()
    assert kept.quantity == Decimal("0.5")
    entry = (await _audit(session, "CANCEL_RECIPE_CHANGE"))[0]
    assert entry.before["DongCongThuc"] == [{"MaNguyenLieu": flour.id, "DinhLuong": 0.5}]
    assert entry.after["TrangThai"] == "Đã hủy"


async def test_deleting_a_dish_cancels_its_pending_changes_with_an_audit_trail(
    api_client, manager_token, session, dish_with_pending_price
):
    async with api_client as client:
        await client.delete(
            f"{CATALOG}/dishes/{dish_with_pending_price.id}", headers=_auth(manager_token)
        )

    rows = (await session.execute(select(DishPriceVersion))).scalars().all()
    assert {row.status for row in rows if row.dish_id == dish_with_pending_price.id} <= {
        "Đã hủy",
        "Đang áp dụng",
        "Hết hiệu lực",
    }
    assert "Chờ áp dụng" not in {row.status for row in rows}
    entries = await _audit(session, "CANCEL_PRICE_CHANGE")
    assert entries and entries[0].reason == "Món bị xóa mềm"


# --- lazy promotion of due versions (FR-CAT-08/20) -----------------------------------------------


async def _price(session, dish_id, price, status, bd, **kw):
    version = DishPriceVersion(
        dish_id=dish_id, price=Decimal(price), business_date=bd, status=status, **kw
    )
    session.add(version)
    await session.flush()
    return version


async def test_a_pending_price_becomes_active_on_its_business_date(session, dish, monkeypatch):
    current = await _price(
        session, dish.id, "40000", "Đang áp dụng", TODAY, effective_from=FIXED_NOW
    )
    pending = await _price(session, dish.id, "45000", "Chờ áp dụng", TODAY + timedelta(days=1))
    await session.commit()

    assert (await active_price_version(session, dish.id, TODAY)).id == current.id
    assert await promote_due_versions(session) == 0
    assert pending.status == "Chờ áp dụng"

    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 25, 7, 0))
    assert (await active_price_version(session, dish.id, date(2026, 9, 25))).id == pending.id
    assert pending.status == "Đang áp dụng"
    assert pending.effective_from == datetime(2026, 9, 25, 6, 0)
    assert current.status == "Hết hiệu lực"
    assert current.effective_to == datetime(2026, 9, 25, 6, 0)
    promotion = (await _audit(session, "PROMOTE_PRICE_VERSION"))[0]
    assert promotion.user_id is None
    assert (promotion.before["TrangThai"], promotion.after["TrangThai"]) == (
        "Chờ áp dụng",
        "Đang áp dụng",
    )


async def test_promotion_is_idempotent(session, dish, monkeypatch):
    await _price(session, dish.id, "40000", "Đang áp dụng", TODAY)
    await _price(session, dish.id, "45000", "Chờ áp dụng", TODAY + timedelta(days=1))
    await session.commit()
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 25, 7, 0))

    assert await promote_due_versions(session) == 1
    session.info.clear()  # a fresh request would not have the in-session shortcut
    assert await promote_due_versions(session) == 0
    assert len(await _audit(session, "PROMOTE_PRICE_VERSION")) == 1
    active = (
        (
            await session.execute(
                select(DishPriceVersion).where(DishPriceVersion.status == "Đang áp dụng")
            )
        )
        .scalars()
        .all()
    )
    assert [row.price for row in active] == [Decimal("45000")]


async def test_a_pending_recipe_becomes_active_and_the_old_one_expires(
    session, dish_with_recipe, flour, monkeypatch
):
    current = await active_recipe(session, dish_with_recipe.id, TODAY)
    pending = Recipe(
        dish_id=dish_with_recipe.id,
        business_date=TODAY + timedelta(days=1),
        status="Chờ áp dụng",
        change_type="Tạo mới",
    )
    session.add(pending)
    await session.flush()
    session.add(RecipeItem(recipe_id=pending.id, ingredient_id=flour.id, quantity=Decimal(1)))
    await session.commit()
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 25, 7, 0))

    promoted = await active_recipe(session, dish_with_recipe.id, date(2026, 9, 25))

    assert promoted.id == pending.id
    assert current.status == "Hết hiệu lực"
    assert len(await _audit(session, "PROMOTE_RECIPE_VERSION")) == 1


async def test_listing_prices_persists_the_promotion(
    api_client, manager_token, session, dish, monkeypatch
):
    await _price(session, dish.id, "40000", "Đang áp dụng", TODAY)
    pending = await _price(session, dish.id, "45000", "Chờ áp dụng", TODAY + timedelta(days=1))
    await session.commit()
    pending_id = pending.id
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 25, 7, 0))
    async with api_client as client:
        response = await client.get(
            f"{CATALOG}/dishes/{dish.id}/prices", headers=_auth(manager_token)
        )
        dishes = await client.get(f"{CATALOG}/dishes", headers=_auth(manager_token))

    states = {row["MaLichSuGia"]: row["TrangThai"] for row in response.json()}
    assert states[pending_id] == "Đang áp dụng"
    assert dishes.json()["items"][0]["GiaHienTai"] == 45000
    await session.rollback()  # nothing but what the endpoint committed survives
    assert (await session.get(DishPriceVersion, pending_id)).status == "Đang áp dụng"


# --- tables (FR-CAT-17..19) --------------------------------------------------------------------


async def _table(session, name="Bàn X", **kw) -> DiningTable:
    table = DiningTable(name=name, **kw)
    session.add(table)
    await session.flush()
    await session.commit()
    return table


async def test_the_cashier_releases_a_table_and_unsent_selections_lapse(
    api_client, cashier_token, session
):
    table = await _table(session, status="Đang phục vụ")
    order = Order(table_id=table.id, business_date=TODAY, order_type="Tại chỗ", status="Đang mở")
    session.add(order)
    await session.flush()
    table.serving_order_id = order.id
    hold = ItemHold(
        selection_id="more",
        owner_id=2,
        table_id=table.id,
        order_id=order.id,
        dish_id=1,
        recipe_id=1,
        price_version_id=1,
        quantity=1,
        expires_at=FIXED_NOW + timedelta(minutes=5),
    )
    session.add(hold)
    await session.commit()
    async with api_client as client:
        released = await client.post(
            f"{CATALOG}/tables/{table.id}/release",
            json={"MaOrder": order.id},
            headers=_auth(cashier_token),
        )
        again = await client.post(
            f"{CATALOG}/tables/{table.id}/release", headers=_auth(cashier_token)
        )

    assert released.status_code == 200, released.text
    assert released.json()["TrangThai"] == "Trống"
    assert released.json()["MaOrderDangPhucVu"] is None
    assert again.status_code == 422
    await session.refresh(hold)
    assert hold.status == "Đã hủy"
    entry = (await _audit(session, "RELEASE_TABLE"))[0]
    assert entry.user_id == 2
    assert entry.before["TrangThai"] == "Đang phục vụ"
    assert entry.before["MaOrderDangPhucVu"] == order.id
    assert entry.after["TrangThai"] == "Trống"


async def test_releasing_for_an_old_order_never_frees_the_table_of_a_new_one(
    api_client, cashier_token, session
):
    table = await _table(session, status="Đang phục vụ")
    new_order = Order(
        table_id=table.id, business_date=TODAY, order_type="Tại chỗ", status="Đang mở"
    )
    session.add(new_order)
    await session.flush()
    table.serving_order_id = new_order.id
    await session.commit()
    async with api_client as client:
        stale = await client.post(
            f"{CATALOG}/tables/{table.id}/release",
            json={"MaOrder": new_order.id + 100},
            headers=_auth(cashier_token),
        )

    assert stale.status_code == 409
    await session.refresh(table)
    assert (table.status, table.serving_order_id) == ("Đang phục vụ", new_order.id)


async def test_the_kitchen_cannot_release_a_table(api_client, warehouse_token, session):
    table = await _table(session, status="Đang phục vụ")
    async with api_client as client:
        response = await client.post(
            f"{CATALOG}/tables/{table.id}/release", headers=_auth(warehouse_token)
        )

    assert response.status_code == 403


async def test_a_serving_table_cannot_be_deleted(api_client, manager_token, session):
    table = await _table(session, status="Đang phục vụ")
    async with api_client as client:
        response = await client.delete(f"{CATALOG}/tables/{table.id}", headers=_auth(manager_token))

    assert response.status_code == 422
    assert (await session.get(DiningTable, table.id)).is_deleted is False


async def test_a_table_never_used_is_deleted_for_good_and_a_used_one_softly(
    api_client, manager_token, session
):
    fresh = await _table(session, "Bàn mới")
    used = await _table(session, "Bàn cũ")
    session.add(
        Order(table_id=used.id, business_date=TODAY, order_type="Tại chỗ", status="Đã thanh toán")
    )
    await session.commit()
    fresh_id, used_id = fresh.id, used.id
    async with api_client as client:
        for table_id in (fresh_id, used_id):
            response = await client.delete(
                f"{CATALOG}/tables/{table_id}", headers=_auth(manager_token)
            )
            assert response.status_code == 204

    session.expire_all()
    assert await session.get(DiningTable, fresh_id) is None
    assert (await session.get(DiningTable, used_id)).is_deleted is True
    assert [e.before["TenBan"] for e in await _audit(session, "DELETE_TABLE")] == [
        "Bàn mới",
        "Bàn cũ",
    ]


async def test_table_names_are_unique_and_editable(api_client, manager_token, session):
    async with api_client as client:
        created = await client.post(
            f"{CATALOG}/tables",
            json={"TenBan": "Bàn 1", "SoChoNgoi": 4},
            headers=_auth(manager_token),
        )
        duplicate = await client.post(
            f"{CATALOG}/tables", json={"TenBan": "Bàn 1"}, headers=_auth(manager_token)
        )
        tid = created.json()["MaBan"]
        renamed = await client.patch(
            f"{CATALOG}/tables/{tid}",
            json={"TenBan": "Bàn VIP", "SoChoNgoi": 6},
            headers=_auth(manager_token),
        )

    assert created.json()["SoChoNgoi"] == 4
    assert duplicate.status_code == 409
    assert renamed.json()["TenBan"] == "Bàn VIP"
    entry = (await _audit(session, "UPDATE_TABLE"))[0]
    assert (entry.before["TenBan"], entry.after["TenBan"]) == ("Bàn 1", "Bàn VIP")


# --- ingredients: audit and unit lock ------------------------------------------------------------


async def test_ingredient_changes_carry_before_and_after(api_client, manager_token, session):
    async with api_client as client:
        created = await client.post(
            f"{CATALOG}/ingredients",
            json={"TenNguyenLieu": "Hành", "DonViTinh": "kg"},
            headers=_auth(manager_token),
        )
        iid = created.json()["MaNguyenLieu"]
        await client.patch(
            f"{CATALOG}/ingredients/{iid}",
            json={"TenNguyenLieu": "Hành lá"},
            headers=_auth(manager_token),
        )
        await client.delete(f"{CATALOG}/ingredients/{iid}", headers=_auth(manager_token))

    update = (await _audit(session, "UPDATE_INGREDIENT"))[0]
    assert (update.before["TenNguyenLieu"], update.after["TenNguyenLieu"]) == ("Hành", "Hành lá")
    delete = (await _audit(session, "DELETE_INGREDIENT"))[0]
    assert delete.before["TenNguyenLieu"] == "Hành lá"
    assert await session.get(Ingredient, iid) is None  # never referenced: removed for good
