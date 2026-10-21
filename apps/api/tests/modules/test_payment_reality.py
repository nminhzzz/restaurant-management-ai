"""Production-grade payment rules: invoice numbering, refunds, polling, expiry.

These cover the gaps that matter once real money moves: a stored invoice number,
a reference for every refund, and a bank-listing fallback when a webhook is late
or was missed.
"""

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.catalog.models import DiningTable
from app.modules.sales import payments
from app.modules.sales.gateways import sepay
from app.modules.sales.models import Invoice, PaymentException, PaymentTransaction
from app.shared import business_date
from tests.helpers import FIXED_NOW
from tests.modules.test_sales_payments import _headers, _make_client, _setup, _submit


async def _second_table(session) -> DiningTable:
    table = DiningTable(name="Bàn 2", is_deleted=False, status="Trống")
    session.add(table)
    await session.flush()
    await session.commit()
    return table


@pytest.mark.anyio
async def test_invoice_numbers_are_sequential_for_a_business_date(session):
    dish, table = await _setup(session)
    other = await _second_table(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)

    first = await _submit(session, client, headers, dish, table)
    second = await _submit(session, client, headers, dish, other)

    paid = []
    for order_id in (first, second):
        response = await client.post(f"/api/v1/sales/orders/{order_id}/pay/cash", headers=headers)
        assert response.status_code == 200, response.text
        paid.append(response.json()["invoice"]["SoHoaDon"])

    day = FIXED_NOW.date()
    assert paid == [f"HD-{day:%Y%m%d}-0001", f"HD-{day:%Y%m%d}-0002"]

    stored = (
        await session.execute(select(Invoice.invoice_number).where(Invoice.order_id == first))
    ).scalar_one()
    assert stored == paid[0]

    payload = await client.get(f"/api/v1/sales/orders/{first}/invoice", headers=headers)
    assert payload.json()["SoHoaDon"] == paid[0]


@pytest.mark.anyio
async def test_refund_requires_a_bank_reference_and_is_stored(session):
    await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session, role="MANAGER")
    exception = PaymentException(
        bank_ref="sepay:7788",
        amount=Decimal("50000"),
        status="Chờ xử lý",
        reason="Không khớp order",
        business_date=business_date.business_date_of(business_date.now()),
    )
    session.add(exception)
    await session.flush()
    await session.commit()

    missing = await client.post(
        f"/api/v1/sales/payment-exceptions/{exception.id}/resolve",
        json={"outcome": "refunded", "note": "Khách đã nhận lại tiền"},
        headers=headers,
    )
    assert missing.status_code == 422
    assert "tham chiếu" in missing.json()["error"]["message"].lower()

    partial = await client.post(
        f"/api/v1/sales/payment-exceptions/{exception.id}/resolve",
        json={
            "outcome": "refunded",
            "note": "Hoàn một phần vì lệch phí",
            "refund_ref": "REF-2026-0001",
            "refund_amount": "20000",
        },
        headers=headers,
    )
    assert partial.status_code == 200, partial.text

    await session.refresh(exception)
    assert exception.status == "Đã hoàn tiền"
    assert exception.refund_ref == "REF-2026-0001"
    assert Decimal(str(exception.refund_amount)) == Decimal("20000")

    listing = await client.get("/api/v1/sales/payment-exceptions?status=", headers=headers)
    row = listing.json()["items"][0]
    assert row["MaThamChieuHoan"] == "REF-2026-0001"
    assert float(row["SoTienHoan"]) == 20000.0


@pytest.mark.anyio
async def test_refund_cannot_exceed_the_received_amount(session):
    await _setup(session)
    exception = PaymentException(
        bank_ref="sepay:7790",
        amount=Decimal("50000"),
        status="Chờ xử lý",
        business_date=business_date.business_date_of(business_date.now()),
    )
    session.add(exception)
    await session.flush()

    with pytest.raises(BusinessRuleError):
        await payments.resolve_exception(
            session,
            exception.id,
            outcome="refunded",
            actor_id=1,
            note="Hoàn quá số nhận",
            refund_ref="REF-X",
            refund_amount=Decimal("60000"),
        )


@pytest.mark.anyio
async def test_refunding_a_wrong_amount_frees_the_order_to_pay_again(session, monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
    monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
    monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "hook-key")
    monkeypatch.setenv("SEPAY_API_TOKEN", "api-token")
    get_settings.cache_clear()

    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id = await _submit(session, client, headers, dish, table)
    started = await client.post(f"/api/v1/sales/orders/{order_id}/pay/qr", headers=headers)
    payment_id = started.json()["MaGiaoDich"]

    # Guest transfers 1.000đ short: the money is kept, the order waits for a human.
    outcome = await payments.handle_sepay_transfer(
        session,
        {
            "id": "9300",
            "transferType": "in",
            "transferAmount": 49000,
            "code": f"TT{payment_id}",
            "content": f"TT{payment_id}",
        },
    )
    assert outcome == "reconciling"
    order = await session.get(payments.Order, order_id)
    await session.refresh(order)
    assert order.status == payments.QR_RECONCILING

    exception = (
        await session.execute(
            select(PaymentException).where(PaymentException.bank_ref == "sepay:9300")
        )
    ).scalar_one()
    await payments.resolve_exception(
        session,
        exception.id,
        outcome="refunded",
        actor_id=1,
        note="Đã hoàn lại tiền cho khách",
        refund_ref="REF-9300",
    )
    await session.refresh(order)
    refreshed = await session.get(PaymentTransaction, payment_id)
    await session.refresh(refreshed)
    assert order.status == "Đang mở"
    assert refreshed.status == payments.QR_CANCELLED
    assert exception.refund_ref == "REF-9300"

    get_settings.cache_clear()


@pytest.mark.anyio
async def test_check_polls_the_bank_after_the_qr_expires(session, monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
    monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
    monkeypatch.setenv("SEPAY_ACCOUNT_NAME", "NHA HANG DEMO")
    monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "hook-key")
    monkeypatch.setenv("SEPAY_API_TOKEN", "api-token")
    get_settings.cache_clear()

    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id = await _submit(session, client, headers, dish, table)
    started = await client.post(f"/api/v1/sales/orders/{order_id}/pay/qr", headers=headers)
    payment_id = started.json()["MaGiaoDich"]

    payment = await session.get(PaymentTransaction, payment_id)
    payment.status = payments.QR_EXPIRED
    payment.deadline = FIXED_NOW - timedelta(minutes=1)
    await session.commit()

    async def fake_listing(**_kwargs):
        return [
            {
                "id": "9001",
                "amount_in": str(int(Decimal(str(payment.amount)))),
                "transaction_content": f"TT{payment_id}",
                "reference_number": "FT9001",
                "code": f"TT{payment_id}",
            }
        ]

    monkeypatch.setattr(sepay, "recent_transfers", fake_listing)

    response = await client.post(f"/api/v1/sales/payments/{payment_id}/check", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["TrangThai"] == payments.QR_SUCCESS

    invoices = await session.execute(
        text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder = :id"), {"id": order_id}
    )
    assert invoices.scalar_one() == 1

    get_settings.cache_clear()


@pytest.mark.anyio
async def test_sync_settles_a_transfer_when_no_webhook_arrives(
    session, session_factory, monkeypatch
):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
    monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
    monkeypatch.setenv("SEPAY_ACCOUNT_NAME", "NHA HANG DEMO")
    monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "hook-key")
    monkeypatch.setenv("SEPAY_API_TOKEN", "api-token")
    get_settings.cache_clear()

    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, cashier = await _headers(session)
    order_id = await _submit(session, client, headers, dish, table)
    started = await client.post(f"/api/v1/sales/orders/{order_id}/pay/qr", headers=headers)
    payment_id = started.json()["MaGiaoDich"]

    async def fake_listing(**_kwargs):
        return [
            {
                "id": "9100",
                "amount_in": "50000.00",
                "transaction_content": f"TT{payment_id}",
                "reference_number": "FT9100",
                "code": f"TT{payment_id}",
            }
        ]

    monkeypatch.setattr(sepay, "recent_transfers", fake_listing)

    assert await payments.sync_recent_transfers(factory=session_factory) == 1
    invoice = (
        await session.execute(select(Invoice).where(Invoice.order_id == order_id))
    ).scalar_one()
    # Nobody clicks "confirm" for a bank transfer, so the invoice names the cashier
    # who opened the order instead of staying blank.
    assert invoice.issued_by == cashier.id
    assert invoice.invoice_number is not None
    assert (
        await session.execute(
            text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder = :id"), {"id": order_id}
        )
    ).scalar_one() == 1

    # The same transfer in the next listing must not settle twice.
    assert await payments.sync_recent_transfers(factory=session_factory) == 0
    assert (
        await session.execute(
            text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder = :id"), {"id": order_id}
        )
    ).scalar_one() == 1

    get_settings.cache_clear()


@pytest.mark.anyio
async def test_sync_ignores_transfers_that_do_not_reference_an_order(
    session, session_factory, monkeypatch
):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
    monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
    monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "hook-key")
    monkeypatch.setenv("SEPAY_API_TOKEN", "api-token")
    get_settings.cache_clear()

    async def fake_listing(**_kwargs):
        return [
            {
                "id": "9200",
                "amount_in": "1500000.00",
                "transaction_content": "TIEN THUE MAT BANG",
                "reference_number": "FT9200",
                "code": None,
            }
        ]

    monkeypatch.setattr(sepay, "recent_transfers", fake_listing)

    assert await payments.sync_recent_transfers(factory=session_factory) == 0
    assert (
        await session.execute(text("SELECT COUNT(*) FROM NGOAI_LE_THANH_TOAN"))
    ).scalar_one() == 0

    get_settings.cache_clear()


@pytest.mark.anyio
async def test_expiry_tick_commits_expired_qr(session, session_factory):
    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id = await _submit(session, client, headers, dish, table)
    started = await client.post(f"/api/v1/sales/orders/{order_id}/pay/qr", headers=headers)
    payment_id = started.json()["MaGiaoDich"]

    payment = await session.get(PaymentTransaction, payment_id)
    payment.deadline = FIXED_NOW - timedelta(minutes=1)
    await session.commit()

    assert await payments.expire_qr_tick(factory=session_factory) >= 1

    refreshed = await session.get(PaymentTransaction, payment_id)
    await session.refresh(refreshed)
    assert refreshed.status == payments.QR_EXPIRED


@pytest.mark.anyio
async def test_duplicate_bank_reference_is_rejected(session):
    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    first = await _submit(session, client, headers, dish, table)
    other = await _second_table(session)
    second = await _submit(session, client, headers, dish, other)

    for order_id, ref in ((first, "FT-1"), (second, "FT-2")):
        qr = await client.post(f"/api/v1/sales/orders/{order_id}/pay/qr", headers=headers)
        payment_id = qr.json()["MaGiaoDich"]
        response = await client.post(
            f"/api/v1/sales/payments/{payment_id}/reference",
            json={"bank_ref": ref},
            headers=headers,
        )
        assert response.status_code == 200, response.text

    second_payment = (
        await session.execute(
            select(PaymentTransaction).where(PaymentTransaction.order_id == second)
        )
    ).scalar_one()
    with pytest.raises(BusinessRuleError):
        await payments.record_bank_reference(session, second_payment.id, "FT-1")


@pytest.mark.anyio
async def test_reprint_uses_the_issued_snapshot(session):
    """FR-SALE-26: renaming or re-pricing a dish must not rewrite old invoices."""
    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id = await _submit(session, client, headers, dish, table)
    paid = await client.post(f"/api/v1/sales/orders/{order_id}/pay/cash", headers=headers)
    assert paid.status_code == 200

    dish.name = "Tên mới sau khi in"
    await session.commit()

    invoice = await client.get(f"/api/v1/sales/orders/{order_id}/invoice", headers=headers)
    assert invoice.status_code == 200
    assert invoice.json()["lines"][0]["TenMon"] == "Món"
    assert invoice.json()["SoHoaDon"] == paid.json()["invoice"]["SoHoaDon"]


@pytest.mark.anyio
async def test_a_provisional_bill_creates_no_invoice(session):
    """FR-SALE-21: the pre-payment bill is a printout, not a revenue record."""
    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    order_id = await _submit(session, client, headers, dish, table)

    response = await client.get(
        f"/api/v1/sales/orders/{order_id}/provisional-invoice", headers=headers
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["TieuDe"].startswith("PHIẾU TẠM TÍNH")
    assert float(body["TongTien"]) == 50000
    assert (
        await session.execute(
            text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder = :id"), {"id": order_id}
        )
    ).scalar_one() == 0
