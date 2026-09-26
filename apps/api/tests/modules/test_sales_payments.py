"""Task 4 payments."""

import hashlib
import hmac
from datetime import datetime, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import (
    DiningTable,
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
async def test_qr_response_carries_a_ten_minute_deadline(session):
    """FR-SALE-15: the countdown needs both timestamps in the response body."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)

    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)

    body = r.json()
    created = datetime.fromisoformat(body["ThoiDiemTaoQR"])
    deadline = datetime.fromisoformat(body["ThoiDiemHetHan"])
    assert deadline - created == timedelta(minutes=10)


@pytest.mark.anyio
async def test_qr_expires_after_ten_minutes_on_get_order(session, monkeypatch):
    """FR-SALE-17: expiry happens lazily, driven by the clock seam, on a GET order read."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    created = datetime.fromisoformat(r.json()["ThoiDiemTaoQR"])

    monkeypatch.setattr(business_date, "now", lambda: created + timedelta(minutes=11))
    r2 = await client.get(f"/api/v1/sales/orders/{oid}", headers=h)
    assert r2.status_code == 200

    from app.modules.sales.models import PaymentTransaction

    pid = r.json()["MaGiaoDich"]
    pay = await session.get(PaymentTransaction, pid)
    assert pay.status == "Hết hạn"


@pytest.mark.anyio
async def test_new_qr_allowed_after_expiry(session, monkeypatch):
    """FR-SALE-17: once expired, the cashier can open a fresh QR for the same order."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    created = datetime.fromisoformat(r.json()["ThoiDiemTaoQR"])

    monkeypatch.setattr(business_date, "now", lambda: created + timedelta(minutes=11))
    r2 = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    assert r2.status_code == 201


@pytest.mark.anyio
async def test_expired_qr_can_move_order_to_reconciliation(session, monkeypatch):
    """FR-SALE-17: an order with an expired QR can be flagged for reconciliation."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]
    created = datetime.fromisoformat(r.json()["ThoiDiemTaoQR"])

    monkeypatch.setattr(business_date, "now", lambda: created + timedelta(minutes=11))
    r2 = await client.post(
        f"/api/v1/sales/orders/{oid}/reconcile", json={"payment_id": pid}, headers=h
    )
    assert r2.status_code == 200
    assert r2.json()["TrangThai"] == "Chờ đối soát"
    assert await order_status(session, oid) == "Chờ đối soát"


@pytest.mark.anyio
async def test_list_payments_for_order(session):
    """The UI recovers the live QR transaction after a reload via this listing."""
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]

    rr = await client.get(f"/api/v1/sales/orders/{oid}/payments", headers=h)
    assert rr.status_code == 200
    items = rr.json()["items"]
    assert items[0]["MaGiaoDich"] == pid
    assert items[0]["TrangThai"] == "Chờ xác nhận"


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


@pytest.mark.anyio
async def test_a_cancelled_line_is_not_charged(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": t.id,
            "lines": [{"MaMon": d.id, "SoLuong": 1}, {"MaMon": d.id, "SoLuong": 1}],
        },
        headers=h,
    )
    oid = r.json()["MaOrder"]
    detail = (await client.get(f"/api/v1/sales/orders/{oid}", headers=h)).json()
    line_id = detail["lines"][1]["MaChiTietOrder"]
    cancel = await client.post(
        f"/api/v1/sales/orders/{oid}/lines/{line_id}/cancel",
        json={"reason": "Khách đổi món"},
        headers=h,
    )
    assert cancel.status_code == 200, cancel.text

    paid = await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)

    assert paid.json()["invoice"]["TongTien"] == 50000


@pytest.mark.anyio
async def test_expire_does_not_clobber_a_confirmation_landing_mid_expire(session, monkeypatch):
    """Lost-update guard (review #1): a confirmation that lands mid-expire must win.

    A confirming write is injected right before the row-touching statement
    `expire_stale_qr` itself issues (via a connection event), so this proves the
    fix's WHERE-conditioned write re-checks status at write time — regardless of
    whether the implementation reads-then-writes per row (the old code) or issues
    one conditional statement (the fix).
    """
    from sqlalchemy import event

    from app.modules.sales.payments import expire_stale_qr

    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]
    created = datetime.fromisoformat(r.json()["ThoiDiemTaoQR"])

    sync_engine = session.get_bind()
    fired = {"done": False}

    def confirm_just_before_the_write(conn, cursor, statement, parameters, context, executemany):
        upper = statement.upper()
        if fired["done"] or "UPDATE" not in upper or "GIAO_DICH_THANH_TOAN" not in upper:
            return
        fired["done"] = True
        conn.exec_driver_sql(
            "UPDATE GIAO_DICH_THANH_TOAN SET TrangThai='Thành công' WHERE MaGiaoDich=?",
            (pid,),
        )

    event.listen(sync_engine, "before_cursor_execute", confirm_just_before_the_write)
    try:
        monkeypatch.setattr(business_date, "now", lambda: created + timedelta(minutes=11))
        await expire_stale_qr(session)
        await session.commit()
    finally:
        event.remove(sync_engine, "before_cursor_execute", confirm_just_before_the_write)

    assert fired["done"], "the injected confirmation never ran — test setup is broken"
    assert await payment_status(session, oid) == "Thành công"


@pytest.mark.anyio
async def test_mark_for_reconciliation_refuses_when_order_already_settled(session):
    """Lost-update guard (review #1): a settled order can't be pushed back to reconciliation."""
    from sqlalchemy import text as sql_text

    from app.core.errors import BusinessRuleError
    from app.modules.sales.payments import mark_for_reconciliation

    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]

    await session.execute(
        sql_text("UPDATE GIAO_DICH_THANH_TOAN SET TrangThai='Hết hạn' WHERE MaGiaoDich=:id"),
        {"id": pid},
    )
    await session.execute(
        sql_text("UPDATE `ORDER` SET TrangThai='Đã thanh toán' WHERE MaOrder=:id"), {"id": oid}
    )
    await session.commit()

    with pytest.raises(BusinessRuleError):
        await mark_for_reconciliation(session, pid)
    await session.commit()

    assert await order_status(session, oid) == "Đã thanh toán"


@pytest.mark.anyio
async def test_cancel_qr_refuses_a_payment_confirmed_behind_its_back(session):
    """Lost-update guard (review #1): can't cancel a QR that was just confirmed."""
    from sqlalchemy import text as sql_text

    from app.core.errors import BusinessRuleError
    from app.modules.sales.models import PaymentTransaction
    from app.modules.sales.payments import cancel_qr

    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    pid = r.json()["MaGiaoDich"]

    stale_ref = await session.get(PaymentTransaction, pid)
    await session.execute(
        sql_text("UPDATE GIAO_DICH_THANH_TOAN SET TrangThai='Thành công' WHERE MaGiaoDich=:id"),
        {"id": pid},
    )
    await session.commit()
    assert stale_ref.status == "Chờ xác nhận"

    with pytest.raises(BusinessRuleError):
        await cancel_qr(session, pid)
    await session.commit()

    assert await payment_status(session, oid) == "Thành công"
