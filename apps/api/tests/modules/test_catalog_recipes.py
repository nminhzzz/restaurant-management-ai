import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import latest_audit, pending_recipe_versions, today


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="MANAGER"):
    await seed_reference_data(session)
    uname = {"MANAGER": "quanly01", "CASHIER": "thungan01", "WAREHOUSE": "kho01"}[role]
    r = await session.execute(select(User).where(User.username == uname))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=uname,
            password_hash=hash_password("pass123"),
            full_name=uname,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    return {
        "Authorization": f"Bearer {create_access_token(str(u.id), {'role': u.role_id, 'username': u.username})}"
    }


async def list_recipes(client, headers, dish_id):
    return await client.get(f"/api/v1/catalog/dishes/{dish_id}/recipes", headers=headers)


async def assign_recipe(client, headers, dish_id, items):
    return await client.post(
        f"/api/v1/catalog/dishes/{dish_id}/recipes/assign",
        json={"items": [{"MaNguyenLieu": iid, "SoLuong": str(qty)} for iid, qty in items]},
        headers=headers,
    )


async def schedule_recipe(client, headers, dish_id, items, on=None):
    body = {"items": [{"MaNguyenLieu": iid, "SoLuong": str(qty)} for iid, qty in items]}
    if on is not None:
        body["BusinessDateApDung"] = on.isoformat()
    return await client.post(
        f"/api/v1/catalog/dishes/{dish_id}/recipes/schedule", json=body, headers=headers
    )


async def cancel_recipe_change(client, headers, rid):
    return await client.delete(f"/api/v1/catalog/recipes/{rid}", headers=headers)


async def apply_recipe_now(client, headers, dish_id, items):
    return await client.post(
        f"/api/v1/catalog/dishes/{dish_id}/recipes/apply-now",
        json={"items": [{"MaNguyenLieu": iid, "SoLuong": str(qty)} for iid, qty in items]},
        headers=headers,
    )


async def get_dish(session, dish_id):
    from app.modules.catalog.models import Dish

    return await session.get(Dish, dish_id)


async def active_recipe(session, dish_id, bd=None):
    from tests.helpers import active_recipe as _ar

    return await _ar(session, dish_id, bd)


async def recipe_items(session, recipe_id):
    from tests.helpers import recipe_items as _ri

    return await _ri(session, recipe_id)


@pytest.mark.asyncio
async def test_the_first_recipe_activates_the_dish(session, draft_dish, flour):
    h = await _headers(session)
    async with await _make_client(session) as c:
        await assign_recipe(c, h, draft_dish.id, items=[(flour.id, "0.2")])
    app.dependency_overrides.clear()
    dish = await get_dish(session, draft_dish.id)
    # dish status derived: should not be Nháp
    from tests.helpers import display_status

    status = await display_status(session, dish)
    assert status in {"Hoạt động", "Hết nguyên liệu"}


@pytest.mark.asyncio
async def test_a_recipe_line_carries_no_unit_of_its_own(session, draft_dish, flour):
    h = await _headers(session)
    async with await _make_client(session) as c:
        await assign_recipe(c, h, draft_dish.id, items=[(flour.id, "0.2")])
    app.dependency_overrides.clear()
    recipe = await active_recipe(session, draft_dish.id, today())
    assert recipe is not None
    rid = recipe["MaCongThuc"] if "MaCongThuc" in recipe else getattr(recipe, "id", None)
    items = await recipe_items(session, int(rid))
    assert (
        items[0]["MaNguyenLieu"] == flour.id or getattr(items[0], "ingredient_id", None) == flour.id
    )
    # no unit field
    assert "DonViTinh" not in (items[0] if isinstance(items[0], dict) else {})


@pytest.mark.asyncio
async def test_only_one_pending_recipe_change_per_dish(session, dish_with_recipe, flour):
    h = await _headers(session)
    async with await _make_client(session) as c:
        await schedule_recipe(c, h, dish_with_recipe.id, items=[(flour.id, "0.3")])
        await schedule_recipe(c, h, dish_with_recipe.id, items=[(flour.id, "0.4")])
    app.dependency_overrides.clear()
    assert len(await pending_recipe_versions(session, dish_with_recipe.id)) == 1


@pytest.mark.asyncio
async def test_cancelling_a_pending_recipe_change_is_audited(session, dish_with_recipe, flour):
    h = await _headers(session)
    async with await _make_client(session) as c:
        created = await schedule_recipe(c, h, dish_with_recipe.id, items=[(flour.id, "0.3")])
        rid = created.json()["MaCongThuc"]
        await cancel_recipe_change(c, h, rid)
    app.dependency_overrides.clear()
    assert (await latest_audit(session))["LoaiThaoTac"] == "CANCEL_RECIPE_CHANGE"


@pytest.mark.asyncio
async def test_a_zero_or_negative_quantity_is_rejected(session, dish_with_recipe, flour):
    h = await _headers(session)
    async with await _make_client(session) as c:
        resp = await schedule_recipe(c, h, dish_with_recipe.id, items=[(flour.id, "0")])
    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_applying_a_recipe_now_creates_a_new_active_version(session, dish_with_recipe, flour):
    old_recipe = await active_recipe(session, dish_with_recipe.id, today())
    old_id = old_recipe["MaCongThuc"]
    h = await _headers(session)
    async with await _make_client(session) as c:
        resp = await apply_recipe_now(c, h, dish_with_recipe.id, items=[(flour.id, "0.5")])
    app.dependency_overrides.clear()
    assert resp.status_code == 201
    new_recipe = await active_recipe(session, dish_with_recipe.id, today())
    new_id = new_recipe["MaCongThuc"]
    assert new_id != old_id
    items = await recipe_items(session, int(new_id))
    assert float(items[0]["SoLuong"]) == 0.5


@pytest.mark.asyncio
async def test_applying_a_recipe_now_leaves_a_scheduled_pending_change_untouched(
    session, dish_with_recipe, flour
):
    h = await _headers(session)
    async with await _make_client(session) as c:
        scheduled = await schedule_recipe(c, h, dish_with_recipe.id, items=[(flour.id, "0.3")])
        pending_id = scheduled.json()["MaCongThuc"]
        await apply_recipe_now(c, h, dish_with_recipe.id, items=[(flour.id, "0.6")])
    app.dependency_overrides.clear()
    pending = await pending_recipe_versions(session, dish_with_recipe.id)
    assert len(pending) == 1
    still_pending_id = pending[0]["MaCongThuc"] if "MaCongThuc" in pending[0] else pending[0].id
    assert int(still_pending_id) == pending_id


@pytest.mark.asyncio
async def test_applying_a_recipe_now_is_audited(session, dish_with_recipe, flour):
    h = await _headers(session)
    async with await _make_client(session) as c:
        await apply_recipe_now(c, h, dish_with_recipe.id, items=[(flour.id, "0.4")])
    app.dependency_overrides.clear()
    assert (await latest_audit(session))["LoaiThaoTac"] == "APPLY_RECIPE_DIRECTLY"


@pytest.mark.asyncio
async def test_listing_recipes_shows_the_pending_change_and_current_lines(
    session, dish_with_recipe, flour
):
    h = await _headers(session)
    async with await _make_client(session) as c:
        scheduled = await schedule_recipe(c, h, dish_with_recipe.id, items=[(flour.id, "0.3")])
        resp = await list_recipes(c, h, dish_with_recipe.id)
    app.dependency_overrides.clear()
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    by_status = {row["TrangThai"]: row for row in body}
    assert "Nháp" in by_status
    assert "Hiệu lực" in by_status
    assert by_status["Nháp"]["MaCongThuc"] == scheduled.json()["MaCongThuc"]
    pending_line = by_status["Nháp"]["items"][0]
    assert pending_line["MaNguyenLieu"] == flour.id
    assert pending_line["TenNguyenLieu"] == flour.name
    assert pending_line["DonViTinh"] == flour.unit
    assert float(pending_line["SoLuong"]) == 0.3


@pytest.mark.asyncio
async def test_cashier_can_read_recipe_versions_but_not_write(session, dish_with_recipe, flour):
    mgr_headers = await _headers(session, "MANAGER")
    cashier_headers = await _headers(session, "CASHIER")
    async with await _make_client(session) as c:
        read_resp = await list_recipes(c, cashier_headers, dish_with_recipe.id)
        write_resp = await schedule_recipe(
            c, cashier_headers, dish_with_recipe.id, items=[(flour.id, "0.3")]
        )
    app.dependency_overrides.clear()
    assert read_resp.status_code == 200
    assert write_resp.status_code == 403


@pytest.mark.asyncio
async def test_warehouse_cannot_read_recipe_versions(session, dish_with_recipe):
    warehouse_headers = await _headers(session, "WAREHOUSE")
    async with await _make_client(session) as c:
        resp = await list_recipes(c, warehouse_headers, dish_with_recipe.id)
    app.dependency_overrides.clear()
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_listing_recipes_for_a_missing_dish_is_404(session):
    h = await _headers(session)
    async with await _make_client(session) as c:
        resp = await list_recipes(c, h, 999999)
    app.dependency_overrides.clear()
    assert resp.status_code == 404
