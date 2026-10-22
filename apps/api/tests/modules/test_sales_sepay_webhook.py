"""SePay webhook and QR details (FR-SALE-15/16 with the SePay adapter)."""

from datetime import timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.modules.sales.gateways import sepay
from app.shared import business_date
from tests.helpers import FIXED_NOW, latest_audit, order_status, payment_status
from tests.modules.test_sales_payments import _headers, _make_client, _setup, _submit

HOOK = "/api/v1/sales/webhooks/sepay"


@pytest.fixture
def sepay_env(monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
    monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
    monkeypatch.setenv("SEPAY_ACCOUNT_NAME", "NHA HANG DEMO")
    monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "hook-key")
    monkeypatch.setenv("SEPAY_API_TOKEN", "api-token")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _body(payment_id: int, amount: int, sepay_id: int = 1, direction: str = "in") -> dict:
    return {
        "id": sepay_id,
        "transferType": direction,
        "transferAmount": amount,
        "code": None,
        "content": f"chuyen khoan TT{payment_id}",
        "referenceCode": "FT1",
    }


AUTH = {"Authorization": "Apikey hook-key"}


async def _qr(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    return client, h, oid, r


async def _invoices(session, oid) -> int:
    rr = await session.execute(text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder=:id"), {"id": oid})
    return rr.scalar_one()


@pytest.mark.anyio
async def test_the_qr_response_carries_the_vietqr_details(session, sepay_env):
    _, _, _, r = await _qr(session)
    body = r.json()
    assert body["payment_code"] == f"TT{body['MaGiaoDich']}"
    assert "amount=50000" in body["qr_image_url"]
    assert body["bank_account"] == "0123499999"


@pytest.mark.anyio
async def test_a_matching_transfer_settles_the_order(session, sepay_env):
    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    resp = await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == {"success": True}
    assert await payment_status(session, oid) == "Thành công"
    assert await order_status(session, oid) == "Đã thanh toán"


@pytest.mark.anyio
async def test_a_wrong_api_key_is_rejected(session, sepay_env):
    client, _, oid, r = await _qr(session)
    resp = await client.post(
        HOOK, json=_body(r.json()["MaGiaoDich"], 50000), headers={"Authorization": "Apikey nope"}
    )
    assert resp.status_code == 401
    assert await order_status(session, oid) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_the_same_transfer_twice_issues_one_invoice(session, sepay_env):
    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    await client.post(HOOK, json=_body(pid, 50000, sepay_id=7), headers=AUTH)
    second = await client.post(HOOK, json=_body(pid, 50000, sepay_id=7), headers=AUTH)
    assert second.status_code == 200
    assert await _invoices(session, oid) == 1


@pytest.mark.anyio
async def test_an_outgoing_transfer_is_ignored(session, sepay_env):
    client, _, oid, r = await _qr(session)
    await client.post(
        HOOK, json=_body(r.json()["MaGiaoDich"], 50000, direction="out"), headers=AUTH
    )
    assert await order_status(session, oid) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_a_transfer_without_our_code_is_acknowledged_but_not_applied(session, sepay_env):
    client, _, oid, _ = await _qr(session)
    body = {**_body(0, 50000), "content": "tien an trua"}
    resp = await client.post(HOOK, json=body, headers=AUTH)
    assert resp.json() == {"success": True}
    assert await order_status(session, oid) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_a_wrong_amount_goes_to_reconciliation(session, sepay_env):
    client, _, oid, r = await _qr(session)
    await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 40000), headers=AUTH)
    assert await order_status(session, oid) == "Chờ đối soát"
    assert await _invoices(session, oid) == 0


@pytest.mark.anyio
async def test_a_transfer_after_expiry_settles_late_and_voids_the_new_qr(
    session, sepay_env, monkeypatch
):
    """FR-SALE-16: late money settles the open order and cancels a newer empty QR."""
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=11))
    await client.get(f"/api/v1/sales/orders/{oid}", headers=h)
    second = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    newer_pid = second.json()["MaGiaoDich"]

    await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)

    assert await order_status(session, oid) == "Đã thanh toán"
    assert await _invoices(session, oid) == 1
    row = await session.execute(
        text("SELECT TrangThai FROM GIAO_DICH_THANH_TOAN WHERE MaGiaoDichTT=:id"),
        {"id": newer_pid},
    )
    assert row.scalar_one() == "Đã hủy"


@pytest.mark.anyio
async def test_money_for_a_reopened_payment_becomes_an_exception(session, sepay_env):
    """FR-SALE-16: a manager already reopened this payment, so do not settle it."""
    client = await _make_client(session)
    h, _ = await _headers(session)
    hm, _ = await _headers(session, role="MANAGER", username="boss")
    d, t = await _setup(session)
    oid = await _submit(session, client, h, d, t)
    pid = (await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)).json()["MaGiaoDich"]
    await client.post(f"/api/v1/sales/payments/{pid}/request-verification", headers=h)
    await client.post(
        f"/api/v1/sales/payments/{pid}/reopen", json={"reason": "khách đổi ý"}, headers=hm
    )

    await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)

    assert await order_status(session, oid) == "Đang mở"
    assert await _invoices(session, oid) == 0


@pytest.mark.anyio
async def test_a_closed_unpaid_exception_can_be_applied_once(session, sepay_env):
    """FR-SALE-17(b): applying late money issues exactly one invoice."""
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    await client.post(f"/api/v1/sales/payments/{pid}/request-verification", headers=h)
    hm, _ = await _headers(session, role="MANAGER", username="boss")
    await client.post(
        f"/api/v1/sales/orders/{oid}/close-unpaid", json={"reason": "hết ca"}, headers=hm
    )
    await client.post(HOOK, json=_body(pid, 50000, sepay_id=31), headers=AUTH)

    listing = await client.get("/api/v1/sales/payment-exceptions", headers=hm)
    assert listing.status_code == 200
    items = listing.json()["items"]
    assert len(items) == 1 and items[0]["TrangThai"] == "Chờ xử lý"

    resp = await client.post(
        f"/api/v1/sales/payment-exceptions/{items[0]['MaNgoaiLe']}/resolve",
        json={"outcome": "applied"},
        headers=hm,
    )
    assert resp.status_code == 200
    assert resp.json()["TrangThai"] == "Đã áp dụng"
    assert await order_status(session, oid) == "Đã thanh toán"
    assert await _invoices(session, oid) == 1


@pytest.mark.anyio
async def test_a_duplicate_transfer_can_only_be_refunded(session, sepay_env):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    hm, _ = await _headers(session, role="MANAGER", username="boss")
    await client.post(HOOK, json=_body(pid, 50000, sepay_id=41), headers=AUTH)
    await client.post(HOOK, json=_body(pid, 50000, sepay_id=42), headers=AUTH)

    items = (await client.get("/api/v1/sales/payment-exceptions", headers=hm)).json()["items"]
    assert len(items) == 1
    unpaid = await client.post(
        f"/api/v1/sales/payment-exceptions/{items[0]['MaNgoaiLe']}/resolve",
        json={"outcome": "refunded"},
        headers=hm,
    )
    assert unpaid.status_code == 422

    resp = await client.post(
        f"/api/v1/sales/payment-exceptions/{items[0]['MaNgoaiLe']}/resolve",
        json={
            "outcome": "refunded",
            "note": "đã hoàn tiền mặt tại quầy",
            "refund_ref": "PT-2026-0007",
        },
        headers=hm,
    )
    assert resp.status_code == 200
    assert resp.json()["TrangThai"] == "Đã hoàn tiền"
    assert resp.json()["MaThamChieuHoan"] == "PT-2026-0007"
    assert await _invoices(session, oid) == 1


@pytest.mark.anyio
async def test_the_same_gateway_transfer_creates_one_exception(session, sepay_env):
    client, _, _, _ = await _qr(session)
    body = {**_body(0, 50000, sepay_id=51), "content": "tien an trua"}
    await client.post(HOOK, json=body, headers=AUTH)
    await client.post(HOOK, json=body, headers=AUTH)
    count = await session.execute(text("SELECT COUNT(*) FROM NGOAI_LE_THANH_TOAN"))
    assert count.scalar_one() == 1


@pytest.mark.anyio
async def test_money_for_an_order_already_paid_in_cash_changes_nothing(session, sepay_env):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    await client.post(f"/api/v1/sales/payments/{pid}/cancel", headers=h)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)
    assert await order_status(session, oid) == "Đã thanh toán"
    assert await _invoices(session, oid) == 1


@pytest.mark.anyio
async def test_check_confirms_through_the_transaction_listing(session, sepay_env, monkeypatch):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "transactions": [
                    {
                        "id": "99",
                        "amount_in": "50000.00",
                        "amount_out": "0",
                        "transaction_content": f"TT{pid}",
                        "reference_number": "FT9",
                        "code": f"TT{pid}",
                    }
                ]
            },
        )

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    resp = await client.post(f"/api/v1/sales/payments/{pid}/check", headers=h)

    assert resp.status_code == 200
    assert resp.json()["TrangThai"] == "Thành công"
    assert await order_status(session, oid) == "Đã thanh toán"


@pytest.mark.anyio
async def test_the_sepay_hook_is_absent_under_the_simulator(session):
    client, _, _, r = await _qr(session)
    resp = await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 50000), headers=AUTH)
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_the_simulator_hook_is_absent_when_sepay_is_active(session, sepay_env):
    """Review #2: the forgeable simulator webhook must not stay live once SePay is on."""
    import hashlib
    import hmac as hmac_mod

    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    secret = get_settings().payment_webhook_secret or "test-secret"
    sig = hmac_mod.new(secret.encode(), f"{pid}:50000".encode(), hashlib.sha256).hexdigest()

    resp = await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"payment_id": pid, "amount": 50000, "signature": sig},
    )

    assert resp.status_code == 404
    assert await order_status(session, oid) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_the_simulator_hook_refuses_a_signed_body_without_an_amount(session):
    """Review #2: a missing amount must not let the simulator confirm a payment."""
    import hashlib
    import hmac as hmac_mod

    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    secret = get_settings().payment_webhook_secret or "test-secret"
    sig = hmac_mod.new(secret.encode(), f"{pid}:None".encode(), hashlib.sha256).hexdigest()

    resp = await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"payment_id": pid, "signature": sig},
    )

    assert resp.status_code == 422
    assert await order_status(session, oid) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_a_second_transfer_on_an_already_confirmed_qr_is_recorded_not_reapplied(
    session, sepay_env
):
    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    await client.post(HOOK, json=_body(pid, 50000, sepay_id=1), headers=AUTH)
    resp = await client.post(HOOK, json=_body(pid, 50000, sepay_id=2), headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == {"success": True}
    assert await _invoices(session, oid) == 1
    audit = await latest_audit(session)
    assert audit is not None and audit["LoaiThaoTac"] == "WEBHOOK_UNMATCHED"


@pytest.mark.anyio
async def test_a_transfer_pointing_at_a_cash_payment_id_is_recorded_not_applied(session, sepay_env):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    row = await session.execute(
        text("SELECT MaGiaoDichTT FROM GIAO_DICH_THANH_TOAN WHERE MaOrder=:id"), {"id": oid}
    )
    cash_pid = row.scalar_one()

    resp = await client.post(HOOK, json=_body(cash_pid, 50000), headers=AUTH)

    assert resp.status_code == 200
    assert await order_status(session, oid) == "Đã thanh toán"
    audit = await latest_audit(session)
    assert audit is not None and audit["LoaiThaoTac"] == "WEBHOOK_UNMATCHED"


@pytest.mark.anyio
async def test_check_tolerates_a_sepay_api_failure(session, sepay_env, monkeypatch):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    resp = await client.post(f"/api/v1/sales/payments/{pid}/check", headers=h)

    assert resp.status_code == 200
    assert resp.json()["TrangThai"] == "Chờ xác nhận"
    assert await order_status(session, oid) == "Chờ xác nhận thanh toán"


@pytest.mark.anyio
async def test_check_skips_a_malformed_sepay_listing_row(session, sepay_env, monkeypatch):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "transactions": [
                    {
                        "id": "1",
                        "amount_in": None,
                        "amount_out": "0",
                        "transaction_content": f"TT{pid}",
                        "reference_number": "FTx",
                        "code": f"TT{pid}",
                    }
                ]
            },
        )

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    resp = await client.post(f"/api/v1/sales/payments/{pid}/check", headers=h)

    assert resp.status_code == 200
    assert resp.json()["TrangThai"] == "Chờ xác nhận"
