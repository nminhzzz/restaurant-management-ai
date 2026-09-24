import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import latest_audit


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers_for(session, role="MANAGER"):
    await seed_reference_data(session)
    username = "quanly01" if role == "MANAGER" else "kho01"
    r = await session.execute(select(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass123"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    return {
        "Authorization": f"Bearer {create_access_token(str(u.id), {'role': u.role_id, 'username': u.username})}"
    }


async def create_ingredient(client, headers, name="Bột mì", **kw):
    body = {"TenNguyenLieu": name}
    body.update(kw)
    return await client.post("/api/v1/catalog/ingredients", json=body, headers=headers)


async def update_ingredient(client, headers, iid, **kw):
    body = {}
    if "unit" in kw:
        body["DonViTinh"] = kw.pop("unit")
    if "name" in kw:
        body["TenNguyenLieu"] = kw.pop("name")
    body.update(kw)
    return await client.patch(f"/api/v1/catalog/ingredients/{iid}", json=body, headers=headers)


async def delete_ingredient(client, headers, iid):
    return await client.delete(f"/api/v1/catalog/ingredients/{iid}", headers=headers)


async def list_ingredients(client, headers, search=None):
    params = {}
    if search:
        params["search"] = search
    return await client.get("/api/v1/catalog/ingredients", params=params, headers=headers)


async def create_dish(client, headers, name="Món", group_id=1):
    return await client.post(
        "/api/v1/catalog/dishes", json={"TenMon": name, "MaNhomMon": group_id}, headers=headers
    )


async def create_supplier(client, headers, name="NCC A"):
    return await client.post(
        "/api/v1/catalog/suppliers", json={"TenNhaCungCap": name}, headers=headers
    )


async def get_supplier(client, headers, sid):
    return await client.get(f"/api/v1/catalog/suppliers/{sid}", headers=headers)


async def delete_supplier(client, headers, sid):
    return await client.delete(f"/api/v1/catalog/suppliers/{sid}", headers=headers)


async def get_ingredient(session, iid):
    from app.modules.catalog.models import Ingredient

    return await session.get(Ingredient, iid)


async def get_supplier_row(session, sid):
    from app.modules.catalog.models import Supplier

    return await session.get(Supplier, sid)


@pytest.mark.asyncio
async def test_an_ingredient_without_its_own_threshold_uses_the_default(
    session, config_with_default_threshold
):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        created = await create_ingredient(c, h, name="Bột mì", MucTonToiThieu=None)
    app.dependency_overrides.clear()
    assert created.status_code == 201
    assert float(created.json()["MucTonToiThieu"]) == 7


@pytest.mark.asyncio
async def test_the_unit_is_locked_once_the_ingredient_is_referenced(session, ingredient_in_recipe):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        resp = await update_ingredient(c, h, ingredient_in_recipe.id, unit="lit")
    app.dependency_overrides.clear()
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


@pytest.mark.asyncio
async def test_the_unit_can_still_be_changed_before_any_reference(session, fresh_ingredient):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        resp = await update_ingredient(c, h, fresh_ingredient.id, unit="lit")
    app.dependency_overrides.clear()
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_deleting_a_referenced_ingredient_is_soft_only(session, ingredient_in_recipe):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        await delete_ingredient(c, h, ingredient_in_recipe.id)
    app.dependency_overrides.clear()
    row = await get_ingredient(session, ingredient_in_recipe.id)
    assert row is not None and row.is_deleted is True


@pytest.mark.asyncio
async def test_ingredient_deletion_is_audited(session, fresh_ingredient):
    h = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        await delete_ingredient(c, h, fresh_ingredient.id)
    app.dependency_overrides.clear()
    assert (await latest_audit(session))["LoaiThaoTac"] == "DELETE_INGREDIENT"


@pytest.mark.asyncio
async def test_warehouse_staff_may_manage_ingredients_but_not_dishes(session):
    await seed_reference_data(session)
    # create group for dish test
    from app.modules.catalog.models import DishGroup

    g = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    await session.commit()
    wh = await _headers_for(session, "WAREHOUSE")
    mgr = await _headers_for(session, "MANAGER")
    async with await _make_client(session) as c:
        ok = await create_ingredient(c, wh, name="Hành lá")
        forbidden = await create_dish(c, wh, name="Món", group_id=g.id)
    app.dependency_overrides.clear()
    assert ok.status_code == 201
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_ingredients_can_be_searched_by_name(session, three_ingredients):
    h = await _headers_for(session, "WAREHOUSE")
    async with await _make_client(session) as c:
        found = await list_ingredients(c, h, search="hành")
    app.dependency_overrides.clear()
    assert [x["TenNguyenLieu"] for x in found.json()["items"]] == ["Hành lá"]


@pytest.mark.asyncio
async def test_a_supplier_shows_its_receipt_history(session, supplier_with_receipts):
    h = await _headers_for(session, "WAREHOUSE")
    async with await _make_client(session) as c:
        detail = await get_supplier(c, h, supplier_with_receipts.id)
    app.dependency_overrides.clear()
    assert len(detail.json()["PhieuNhap"]) == 2


@pytest.mark.asyncio
async def test_a_supplier_with_receipts_is_only_soft_deleted(session, supplier_with_receipts):
    h = await _headers_for(session, "WAREHOUSE")
    async with await _make_client(session) as c:
        await delete_supplier(c, h, supplier_with_receipts.id)
    app.dependency_overrides.clear()
    row = await get_supplier_row(session, supplier_with_receipts.id)
    assert row is not None and row.is_deleted is True
    assert (await latest_audit(session))["LoaiThaoTac"] == "DELETE_SUPPLIER"


@pytest.mark.asyncio
async def test_a_supplier_with_no_history_is_deleted_outright(session, fresh_supplier):
    h = await _headers_for(session, "WAREHOUSE")
    async with await _make_client(session) as c:
        await delete_supplier(c, h, fresh_supplier.id)
    app.dependency_overrides.clear()
    assert await get_supplier_row(session, fresh_supplier.id) is None
