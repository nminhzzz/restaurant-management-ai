"""FR-INV-10 — automatic out-of-stock recompute hides/restores a dish."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import (
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
)
from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.enums import VersionStatus


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="WAREHOUSE", username="kho05"):
    await seed_reference_data(session)
    from sqlalchemy import select as sel

    r = await session.execute(sel(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}, u


async def _dish_with_recipe(session, need=3, stock_qty=2):
    g = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    d = Dish(name="Món cần NL", group_id=g.id, is_deleted=False)
    session.add(d)
    await session.flush()
    ing = Ingredient(name="NL hiếm", unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    session.add(ing)
    await session.flush()
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(
        receipt_id=gr.id, ingredient_id=ing.id, quantity=stock_qty, unit_price=1000
    )
    session.add(gl)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ing.id,
            receipt_line_id=gl.id,
            quantity_remaining=stock_qty,
            status="Còn hạn",
            received_at=business_date.now(),
        )
    )
    ing.stock_qty = stock_qty
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    session.add(
        DishPriceVersion(
            dish_id=d.id,
            price=30000,
            business_date=bd,
            status=VersionStatus.HIEU_LUC.value,
            change_type="Tạo mới",
        )
    )
    rc = Recipe(
        dish_id=d.id, business_date=bd, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới"
    )
    session.add(rc)
    await session.flush()
    session.add(RecipeItem(recipe_id=rc.id, ingredient_id=ing.id, quantity=need))
    await session.flush()
    await session.commit()
    return d, ing


@pytest.mark.anyio
async def test_manual_issue_hides_dish_when_recipe_can_no_longer_be_served(session):
    d, ing = await _dish_with_recipe(session, need=3, stock_qty=5)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 4}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    await session.refresh(d)
    assert d.out_of_stock_auto is True


@pytest.mark.anyio
async def test_receipt_restores_dish_once_recipe_can_be_served_again(session):
    d, ing = await _dish_with_recipe(session, need=3, stock_qty=1)
    client = await _make_client(session)
    h, _ = await _headers(session)
    # Force the recompute so the dish starts hidden.
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    await session.refresh(d)
    assert d.out_of_stock_auto is True

    r2 = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1000}]},
        headers=h,
    )
    assert r2.status_code == 201, r2.text
    await session.refresh(d)
    assert d.out_of_stock_auto is False


@pytest.mark.anyio
async def test_stocktake_confirm_recomputes_visibility(session):
    d, ing = await _dish_with_recipe(session, need=3, stock_qty=5)
    client = await _make_client(session)
    h, _ = await _headers(session)
    st = await client.post("/api/v1/inventory/stocktakes", headers=h)
    sid = st.json()["MaPhieuKiemKe"]
    await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/counts",
        json=[{"ingredient_id": ing.id, "actual_qty": 0}],
        headers=h,
    )
    r = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)
    assert r.status_code == 200
    await session.refresh(d)
    assert d.out_of_stock_auto is True
