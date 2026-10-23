"""Regression tests for docs/testing/source-docs-review-2026-10-21.md (P1)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text

from app.modules.catalog.models import DishPriceVersion, Ingredient
from app.modules.inventory.models import GoodsReceipt
from app.modules.sales.models import Invoice, Order, OrderLine, Reservation
from app.shared import business_date
from tests.modules.test_sales_payments import (
    _headers,
    _make_client,
    _setup,
    _submit,
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _order(session, oid: int) -> Order:
    return (await session.execute(select(Order).where(Order.id == oid))).scalar_one()


@pytest.mark.anyio
async def test_negative_quantity_is_rejected(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    detail = (await client.get(f"/api/v1/sales/orders/{oid}", headers=h)).json()
    line_id = detail["lines"][0]["MaChiTietOrder"]

    r = await client.patch(
        f"/api/v1/sales/orders/{oid}/lines/{line_id}",
        json={"quantity": -3},
        headers=h,
    )

    assert r.status_code == 422
    line = await session.get(OrderLine, line_id)
    assert line is not None and line.quantity == 1


@pytest.mark.anyio
async def test_qr_locks_the_order_and_cash(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    detail = (await client.get(f"/api/v1/sales/orders/{oid}", headers=h)).json()
    line_id = detail["lines"][0]["MaChiTietOrder"]

    qr = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    assert qr.status_code == 201
    assert (await _order(session, oid)).status == "Chờ xác nhận thanh toán"

    mutate = await client.patch(
        f"/api/v1/sales/orders/{oid}/lines/{line_id}",
        json={"quantity": 2},
        headers=h,
    )
    cash = await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    assert mutate.status_code == 422
    assert cash.status_code == 422

    pid = qr.json()["MaGiaoDich"]
    await client.post(f"/api/v1/sales/payments/{pid}/cancel", headers=h)
    assert (await _order(session, oid)).status == "Đang mở"


@pytest.mark.anyio
async def test_direct_submit_cannot_take_held_stock(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, user = await _headers(session)

    hold = await client.post(
        "/api/v1/sales/holds",
        json={"table_id": t.id, "dish_id": d.id, "quantity": 18},
        headers=h,
    )
    assert hold.status_code == 201, hold.text

    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 5}]},
        headers=h,
    )

    assert r.status_code == 422
    assert (await session.scalar(select(func.count(Order.id)))) == 0
    assert user is not None


@pytest.mark.anyio
async def test_expired_lot_is_not_sold(session):
    d, t = await _setup(session)
    lot = (
        await session.execute(select(OrderLine).where(OrderLine.dish_id == d.id).limit(1))
    ).scalar_one_or_none()
    assert lot is None
    from app.modules.inventory.models import IngredientLot

    row = (await session.execute(select(IngredientLot))).scalars().first()
    assert row is not None
    row.expiry_date = business_date.business_date_of(business_date.now()) - timedelta(days=1)
    await session.commit()

    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )

    assert r.status_code == 422


@pytest.mark.anyio
async def test_stocktake_blocks_holds_and_holds_block_stocktake(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    hm, _ = await _headers(session, role="MANAGER", username="boss")

    started = await client.post("/api/v1/inventory/stocktakes", headers=hm)
    assert started.status_code == 201, started.text
    blocked_hold = await client.post(
        "/api/v1/sales/holds",
        json={"table_id": t.id, "dish_id": d.id, "quantity": 1},
        headers=h,
    )
    assert blocked_hold.status_code == 422

    # Close that session by deleting the row directly, then create a hold first.
    await session.execute(text("DELETE FROM PHIEU_KIEM_KE"))
    await session.commit()
    hold = await client.post(
        "/api/v1/sales/holds",
        json={"table_id": t.id, "dish_id": d.id, "quantity": 1},
        headers=h,
    )
    assert hold.status_code == 201, hold.text
    blocked_stocktake = await client.post("/api/v1/inventory/stocktakes", headers=hm)
    assert blocked_stocktake.status_code == 422


@pytest.mark.anyio
async def test_cancel_receipt_is_refused_after_stock_was_used(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    hm, _ = await _headers(session, role="MANAGER", username="boss")
    receipt = (await session.execute(select(GoodsReceipt))).scalars().first()
    assert receipt is not None

    await _submit(session, client, h, d, t)
    r = await client.delete(f"/api/v1/inventory/receipts/{receipt.id}", headers=hm)

    assert r.status_code == 422


@pytest.mark.anyio
async def test_deleted_dish_is_blocked_on_hold_and_submit(session):
    d, t = await _setup(session)
    d.is_deleted = True
    await session.commit()
    client = await _make_client(session)
    h, _ = await _headers(session)

    hold = await client.post(
        "/api/v1/sales/holds",
        json={"table_id": t.id, "dish_id": d.id, "quantity": 1},
        headers=h,
    )
    order = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )

    assert hold.status_code == 422
    assert order.status_code == 422


@pytest.mark.anyio
async def test_submit_is_atomic(session):
    d, t = await _setup(session)
    ing = (await session.execute(select(Ingredient))).scalars().first()
    assert ing is not None
    before = Decimal(str(ing.stock_qty))
    client = await _make_client(session)
    h, _ = await _headers(session)

    r = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": t.id,
            "lines": [
                {"MaMon": d.id, "SoLuong": 1},
                {"MaMon": 99999, "SoLuong": 1},
            ],
        },
        headers=h,
    )

    assert r.status_code == 422
    assert (await session.scalar(select(func.count(Order.id)))) == 0
    await session.refresh(ing)
    assert Decimal(str(ing.stock_qty)) == before


@pytest.mark.anyio
async def test_submit_is_idempotent(session):
    d, t = await _setup(session)
    ing = (await session.execute(select(Ingredient))).scalars().first()
    assert ing is not None
    before = Decimal(str(ing.stock_qty))
    client = await _make_client(session)
    h, _ = await _headers(session)
    payload = {
        "MaBan": t.id,
        "request_id": "req-review-1",
        "lines": [{"MaMon": d.id, "SoLuong": 1}],
    }

    first = await client.post("/api/v1/sales/orders", json=payload, headers=h)
    second = await client.post("/api/v1/sales/orders", json=payload, headers=h)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["MaOrder"] == second.json()["MaOrder"]
    assert (await session.scalar(select(func.count(Order.id)))) == 1
    await session.refresh(ing)
    assert Decimal(str(ing.stock_qty)) == before - 1


@pytest.mark.anyio
async def test_bulk_add_is_atomic(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)

    r = await client.post(
        f"/api/v1/sales/orders/{oid}/lines/bulk",
        json={
            "lines": [
                {"dish_id": d.id, "quantity": 1},
                {"dish_id": 99999, "quantity": 1},
            ]
        },
        headers=h,
    )

    assert r.status_code == 422
    lines = (
        await session.execute(select(func.count(OrderLine.id)).where(OrderLine.order_id == oid))
    ).scalar_one()
    assert lines == 1


@pytest.mark.anyio
async def test_hold_created_before_a_price_change_is_refused(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    hold = await client.post(
        "/api/v1/sales/holds",
        json={"table_id": t.id, "dish_id": d.id, "quantity": 1},
        headers=h,
    )
    assert hold.status_code == 201, hold.text
    hold_id = hold.json()["MaGiuCho"]

    session.add(
        DishPriceVersion(
            dish_id=d.id,
            price=99000,
            business_date=business_date.business_date_of(business_date.now()),
            status="Đang áp dụng",
            change_type="Sửa giá",
        )
    )
    await session.commit()

    r = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": t.id,
            "lines": [
                {
                    "MaMon": d.id,
                    "SoLuong": 1,
                    "hold_id": hold_id,
                }
            ],
        },
        headers=h,
    )

    assert r.status_code == 422
    assert "Giá hoặc công thức món đã thay đổi" in r.json()["error"]["message"]
    assert (await session.scalar(select(func.count(Reservation.id)))) == 1


@pytest.mark.anyio
async def test_payment_and_invoice_inherit_the_order_business_date(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    order = await _order(session, oid)
    order.business_date = date.today() - timedelta(days=1)
    await session.commit()

    paid = await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    assert paid.status_code == 200

    invoice = (await session.execute(select(Invoice).where(Invoice.order_id == oid))).scalar_one()
    assert invoice.business_date == order.business_date


@pytest.mark.anyio
async def test_audit_list_accepts_a_system_entry(session):
    from app.shared.audit import SystemAuditLog

    session.add(
        SystemAuditLog(
            user_id=None,
            action="WEBHOOK_UNMATCHED",
            target_entity="NGOAI_LE_THANH_TOAN",
            target_id="test",
        )
    )
    await session.commit()
    client = await _make_client(session)
    hm, _ = await _headers(session, role="MANAGER", username="boss")

    r = await client.get("/api/v1/settings/audit-log", headers=hm)

    assert r.status_code == 200
    assert any(item["MaNguoiDung"] is None for item in r.json()["items"])


@pytest.mark.anyio
async def test_cancelling_one_of_three_lines_does_not_crash(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    created = await client.post(
        "/api/v1/sales/orders",
        json={
            "MaBan": t.id,
            "lines": [{"MaMon": d.id, "SoLuong": 1} for _ in range(3)],
        },
        headers=h,
    )
    assert created.status_code == 201, created.text
    oid = created.json()["MaOrder"]
    detail = (await client.get(f"/api/v1/sales/orders/{oid}", headers=h)).json()
    assert len(detail["lines"]) == 3

    r = await client.post(
        f"/api/v1/sales/orders/{oid}/lines/{detail['lines'][0]['MaChiTietOrder']}/cancel",
        json={"reason": "khách đổi ý"},
        headers=h,
    )

    assert r.status_code == 200
    assert (await _order(session, oid)).status == "Đang mở"
