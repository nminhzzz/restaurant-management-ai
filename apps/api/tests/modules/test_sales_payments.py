"""Task 4 payments."""

import pytest
import hmac, hashlib
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from app.shared.enums import VersionStatus
from app.modules.catalog.models import (
    Dish,
    DishGroup,
    Ingredient,
    Recipe,
    RecipeItem,
    DishPriceVersion,
    DiningTable,
)
from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot
from app.core.config import get_settings

from tests.helpers import order_status, payment_status


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="CASHIER", username="tester"):
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


async def _setup(session):
    g = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    d = Dish(name="Món", group_id=g.id, is_deleted=False)
    session.add(d)
    await session.flush()
    ing = Ingredient(name="NL", unit="kg", min_stock=1, stock_qty=20, is_deleted=False)
    session.add(ing)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    pv = DishPriceVersion(
        dish_id=d.id,
        price=50000,
        business_date=bd,
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    session.add(pv)
    await session.flush()
    rc = Recipe(
        dish_id=d.id, business_date=bd, status=VersionStatus.HIEU_LUC.value, change_type="Tạo mới"
    )
    session.add(rc)
    await session.flush()
    session.add(RecipeItem(recipe_id=rc.id, ingredient_id=ing.id, quantity=1))
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=20, unit_price=1000)
    session.add(gl)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        receipt_line_id=gl.id,
        quantity_remaining=20,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    t = DiningTable(name="Bàn 1", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return d, t


async def _submit(session, client, h, d, t):
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    return r.json()["MaOrder"]


def _sign(pid, amount):
    secret = get_settings().payment_webhook_secret or "test-secret"
    msg = f"{pid}:{amount}"
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()


@pytest.mark.anyio
async def test_cash_payment(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    assert r.status_code == 200
    assert r.json()["invoice"]["SoHoaDon"] is not None
    assert await order_status(session, oid) == "Đã thanh toán"


@pytest.mark.anyio
async def test_qr_starts(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    assert r.status_code == 201
    j = r.json()
    assert j["TrangThai"] == "Chờ xác nhận"


@pytest.mark.anyio
async def test_second_qr_refused(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_webhook_settles(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]
    from tests.helpers import order_count as _oc

    # need amount: order total is 50000
    sig = _sign(pid, 50000)
    r2 = await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"payment_id": pid, "amount": 50000, "signature": sig},
    )
    assert r2.status_code == 200
    assert await payment_status(session, oid) == "Thành công"


@pytest.mark.anyio
async def test_webhook_idempotent(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]
    sig = _sign(pid, 50000)
    await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"payment_id": pid, "amount": 50000, "signature": sig},
    )
    await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"payment_id": pid, "amount": 50000, "signature": sig},
    )
    from sqlalchemy import text

    rr = await session.execute(text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder=:id"), {"id": oid})
    assert rr.scalar_one() == 1


@pytest.mark.anyio
async def test_webhook_bad_sig(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]
    r2 = await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"payment_id": pid, "amount": 50000, "signature": "bad"},
    )
    assert r2.status_code == 401


@pytest.mark.anyio
async def test_cancel_qr(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]
    r2 = await client.post(f"/api/v1/sales/payments/{pid}/cancel", headers=h)
    assert r2.status_code == 200
    assert await payment_status(session, oid) == "Đã hủy"
    r3 = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    assert r3.status_code == 201
