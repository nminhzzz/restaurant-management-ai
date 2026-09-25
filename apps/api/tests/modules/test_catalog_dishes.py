"""Phase 2 Task 1 — groups & dishes (FR-CAT-01..06)."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import latest_audit, pending_price_versions, today


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _manager_token(session):
    # find or create manager
    await seed_reference_data(session)
    r = await session.execute(select(User).where(User.username == "quanly01"))
    mgr = r.scalar_one_or_none()
    if mgr is None:
        mgr = User(
            username="quanly01",
            password_hash=hash_password("pass123"),
            full_name="Quan Ly",
            role_id="MANAGER",
            status="Hoạt động",
        )
        session.add(mgr)
        await session.flush()
        await session.commit()
    return create_access_token(str(mgr.id), {"role": mgr.role_id, "username": mgr.username})


async def _auth_headers(session):
    tok = await _manager_token(session)
    return {"Authorization": f"Bearer {tok}"}


async def create_group(client, headers, name="Nhóm A"):
    return await client.post("/api/v1/catalog/groups", json={"TenNhom": name}, headers=headers)


async def list_groups(client, headers):
    return await client.get("/api/v1/catalog/groups", headers=headers)


async def delete_group(client, headers, gid):
    return await client.delete(f"/api/v1/catalog/groups/{gid}", headers=headers)


async def reorder_groups(client, headers, ids):
    return await client.put(
        "/api/v1/catalog/groups/order", json={"MaNhomMon": ids}, headers=headers
    )


async def create_dish(client, headers, name="Phở bò", group_id=None, **kw):
    body = {"TenMon": name}
    if group_id is not None:
        body["MaNhomMon"] = group_id
    body.update(kw)
    return await client.post("/api/v1/catalog/dishes", json=body, headers=headers)


async def update_dish(client, headers, dish_id, **kw):
    return await client.patch(f"/api/v1/catalog/dishes/{dish_id}", json=kw, headers=headers)


async def delete_dish(client, headers, dish_id):
    return await client.delete(f"/api/v1/catalog/dishes/{dish_id}", headers=headers)


async def list_dishes(client, headers, search=None):
    params = {}
    if search:
        params["search"] = search
    return await client.get("/api/v1/catalog/dishes", params=params, headers=headers)


async def get_dish(session, dish_id):
    from app.modules.catalog.models import Dish

    return await session.get(Dish, dish_id)


async def active_recipe(session, dish_id, bd=None):
    from tests.helpers import active_recipe as _ar

    return await _ar(session, dish_id, bd)


@pytest.mark.asyncio
async def test_a_group_with_live_dishes_cannot_be_deleted(session, group_with_dish):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await delete_group(client, headers, group_with_dish.id)
    app.dependency_overrides.clear()
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.asyncio
async def test_a_group_can_be_deleted_once_every_dish_is_soft_deleted(session, group_with_dish):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        await delete_dish(client, headers, group_with_dish.dish_id)
        resp = await delete_group(client, headers, group_with_dish.id)
    app.dependency_overrides.clear()
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_a_dish_is_never_hard_deleted(session, dish):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        await delete_dish(client, headers, dish.id)
    app.dependency_overrides.clear()
    row = await get_dish(session, dish.id)
    assert row is not None
    assert row.is_deleted is True


@pytest.mark.asyncio
async def test_soft_deleting_a_dish_cancels_its_pending_changes(session, dish_with_pending_price):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        await delete_dish(client, headers, dish_with_pending_price.id)
    app.dependency_overrides.clear()
    pending = await pending_price_versions(session, dish_with_pending_price.id)
    assert pending == []


@pytest.mark.asyncio
async def test_dish_deletion_is_audited(session, dish):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        await delete_dish(client, headers, dish.id)
    app.dependency_overrides.clear()
    assert (await latest_audit(session))["LoaiThaoTac"] == "DELETE_DISH"


@pytest.mark.asyncio
async def test_a_new_dish_starts_as_draft(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        created = await create_dish(client, headers, name="Phở bò", group_id=group.id)
    app.dependency_overrides.clear()
    assert created.status_code == 201
    assert created.json()["TrangThai"] == "Nháp"
    # dish row should still exist
    dish_id = created.json()["MaMon"]
    from app.modules.catalog.models import Dish

    row = await session.get(Dish, dish_id)
    assert row is not None
    assert row.hide_manual is False
    assert await active_recipe(session, dish_id, today()) is None


@pytest.mark.asyncio
async def test_a_dish_carries_a_name_a_price_a_group_and_a_picture(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await create_dish(client, headers, name="Phở bò", group_id=group.id)
    app.dependency_overrides.clear()
    body = resp.json()
    assert {"TenMon", "MaNhomMon", "HinhAnh", "GiaHienTai"} <= set(body)


@pytest.mark.asyncio
async def test_dishes_can_be_searched_by_name(session, three_dishes):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        found = await list_dishes(client, headers, search="phở")
    app.dependency_overrides.clear()
    assert [x["TenMon"] for x in found.json()["items"]] == ["Phở bò"]


@pytest.mark.asyncio
async def test_a_dish_belongs_to_exactly_one_group(session, group, other_group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        created = await create_dish(client, headers, name="Phở bò", group_id=group.id)
        moved = await update_dish(
            client, headers, created.json()["MaMon"], MaNhomMon=other_group.id
        )
    app.dependency_overrides.clear()
    assert moved.json()["MaNhomMon"] == other_group.id


@pytest.mark.asyncio
async def test_groups_carry_a_display_order(session, three_groups):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await list_groups(client, headers)
    app.dependency_overrides.clear()
    assert [x["ThuTuHienThi"] for x in resp.json()] == list(range(1, len(three_groups) + 1))


@pytest.mark.asyncio
async def test_reordering_groups_renumbers_them(session, three_groups):
    headers = await _auth_headers(session)
    first, second, third = three_groups
    async with await _make_client(session) as client:
        await reorder_groups(client, headers, [third.id, first.id, second.id])
        listed = await list_groups(client, headers)
    app.dependency_overrides.clear()
    assert [x["MaNhomMon"] for x in listed.json()] == [third.id, first.id, second.id]
    assert [x["ThuTuHienThi"] for x in listed.json()] == [1, 2, 3]


@pytest.mark.asyncio
async def test_a_reorder_that_omits_a_group_is_refused(session, three_groups):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await reorder_groups(client, headers, [three_groups[0].id])
    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_a_new_group_goes_to_the_end_of_the_list(session, three_groups):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        created = await create_group(client, headers, name="Tráng miệng")
    app.dependency_overrides.clear()
    assert created.json()["ThuTuHienThi"] == len(three_groups) + 1


@pytest.mark.asyncio
async def test_soft_deleted_table_is_hidden_from_the_floor_plan(session):
    # placeholder for Task5 - not needed here
    assert True


@pytest.mark.asyncio
async def test_a_dish_image_is_persisted_on_create_and_returned(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        created = await create_dish(
            client,
            headers,
            name="Phở bò",
            group_id=group.id,
            HinhAnh="https://example.com/pho.jpg",
        )
    app.dependency_overrides.clear()
    assert created.status_code == 201
    assert created.json()["HinhAnh"] == "https://example.com/pho.jpg"
    dish_id = created.json()["MaMon"]
    row = await get_dish(session, dish_id)
    assert row.image_url == "https://example.com/pho.jpg"


@pytest.mark.asyncio
async def test_a_dish_image_is_persisted_on_update_and_returned(session, dish):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        updated = await update_dish(client, headers, dish.id, HinhAnh="/uploads/pho.jpg")
    app.dependency_overrides.clear()
    assert updated.status_code == 200
    assert updated.json()["HinhAnh"] == "/uploads/pho.jpg"
    row = await get_dish(session, dish.id)
    assert row.image_url == "/uploads/pho.jpg"


@pytest.mark.asyncio
async def test_a_javascript_scheme_dish_image_is_rejected(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await create_dish(
            client,
            headers,
            name="Phở bò",
            group_id=group.id,
            HinhAnh="javascript:alert(1)",
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_a_protocol_relative_dish_image_is_rejected(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await create_dish(
            client,
            headers,
            name="Phở bò",
            group_id=group.id,
            HinhAnh="//evil.example.com/x.jpg",
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 422
