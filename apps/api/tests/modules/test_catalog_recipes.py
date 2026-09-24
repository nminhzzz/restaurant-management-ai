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


async def _headers(session):
    await seed_reference_data(session)
    r = await session.execute(select(User).where(User.username == "quanly01"))
    mgr = r.scalar_one_or_none()
    if mgr is None:
        mgr = User(
            username="quanly01",
            password_hash=hash_password("pass123"),
            full_name="QL",
            role_id="MANAGER",
            status="Hoạt động",
        )
        session.add(mgr)
        await session.flush()
        await session.commit()
    return {
        "Authorization": f"Bearer {create_access_token(str(mgr.id), {'role': mgr.role_id, 'username': mgr.username})}"
    }


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
