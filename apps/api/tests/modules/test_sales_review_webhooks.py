"""Gateway webhook security: authentication, bounds, replay, fail-closed (WP-B item 6)."""

import json
import logging

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.modules.sales import webhooks
from app.modules.sales.models import Invoice, PaymentTransaction
from app.shared.audit import SystemAuditLog
from tests.modules.sales_support import api, place_order, sellable, staff, table
from tests.modules.test_sales_sepay_webhook import AUTH, HOOK, _body, _qr


async def _count(session, model) -> int:
    return (await session.execute(select(func.count()).select_from(model))).scalar_one()


async def _status(session, payment_id) -> str:
    return (
        await session.execute(
            select(PaymentTransaction.status).where(PaymentTransaction.id == payment_id)
        )
    ).scalar_one()


@pytest.mark.anyio
async def test_a_transfer_to_another_account_is_ignored(session, sepay_env):
    client, _, _, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    resp = await client.post(
        HOOK, json={**_body(pid, 50000), "accountNumber": "9999999999"}, headers=AUTH
    )
    missing = {k: v for k, v in _body(pid, 50000).items() if k != "accountNumber"}
    resp_missing = await client.post(HOOK, json=missing, headers=AUTH)

    assert resp.status_code == 200 and resp_missing.status_code == 200
    assert await _status(session, pid) == "Chờ xác nhận"
    assert await _count(session, Invoice) == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "mutation",
    [
        {"transferAmount": -50000},
        {"transferAmount": 0},
        {"transferAmount": "NaN"},
        {"transferAmount": "Infinity"},
        {"transferAmount": True},
        {"transferAmount": {"v": 1}},
        {"id": "x" * 65},
        {"id": None},
        {"content": "TT1 " + "z" * 1500},
        {"referenceCode": "r" * 101},
        {"code": "c" * 101},
    ],
)
async def test_malformed_or_oversized_fields_are_ignored(session, sepay_env, mutation):
    client, _, _, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    resp = await client.post(HOOK, json={**_body(pid, 50000), **mutation}, headers=AUTH)

    assert resp.status_code == 200
    assert await _status(session, pid) == "Chờ xác nhận"
    assert await _count(session, Invoice) == 0
    assert await _count(session, PaymentTransaction) == 1


@pytest.mark.anyio
async def test_a_huge_body_is_refused_before_it_is_parsed(session, sepay_env):
    client, _, _, r = await _qr(session)
    huge = json.dumps({**_body(r.json()["MaGiaoDich"], 50000), "pad": "x" * 40_000})

    resp = await client.post(
        HOOK, content=huge, headers={**AUTH, "Content-Type": "application/json"}
    )

    assert resp.status_code == 413
    assert await _count(session, Invoice) == 0


@pytest.mark.anyio
@pytest.mark.parametrize("raw", [b"not json", b"[1, 2]", b"null", b""])
async def test_a_body_that_is_not_a_json_object_is_refused(session, sepay_env, raw):
    client, *_ = await _qr(session)

    resp = await client.post(
        HOOK, content=raw, headers={**AUTH, "Content-Type": "application/json"}
    )

    assert resp.status_code == 422


@pytest.mark.anyio
async def test_a_rejected_call_writes_no_business_row_and_logs_no_secret(
    session,
    sepay_env,
    caplog,
):
    client, _, _, r = await _qr(session)
    audits_before = await _count(session, SystemAuditLog)

    with caplog.at_level(logging.DEBUG):
        resp = await client.post(
            HOOK,
            json=_body(r.json()["MaGiaoDich"], 50000),
            headers={"Authorization": "Apikey super-secret-guess"},
        )

    assert resp.status_code == 401
    assert await _count(session, SystemAuditLog) == audits_before
    assert "super-secret-guess" not in caplog.text and "hook-key" not in caplog.text


@pytest.mark.anyio
async def test_logs_never_carry_the_payload_of_an_unmatched_transfer(
    session,
    sepay_env,
    caplog,
):
    client, *_ = await _qr(session)
    body = {**_body(0, 50000), "content": "bi mat noi dung chuyen khoan 4111111111111111"}

    with caplog.at_level(logging.DEBUG):
        resp = await client.post(HOOK, json=body, headers=AUTH)

    assert resp.json() == {"success": True}
    assert "4111111111111111" not in caplog.text and "bi mat" not in caplog.text


@pytest.mark.anyio
async def test_the_stored_webhook_content_is_bounded_and_secret_free(session, sepay_env):
    client, _, _, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)

    stored = (
        await session.execute(
            select(PaymentTransaction.webhook_content).where(PaymentTransaction.id == pid)
        )
    ).scalar_one()
    assert len(stored) <= 2000 and "hook-key" not in stored and "Apikey" not in stored
    assert json.loads(stored)["transferAmount"] == "50000"


@pytest.mark.anyio
async def test_a_duplicate_delivery_that_loses_the_unique_key_race_is_acknowledged(
    session,
    sepay_env,
    monkeypatch,
):
    client, _, _, r = await _qr(session)

    async def lose_the_race(*_args, **_kwargs):
        raise IntegrityError("INSERT", {}, Exception("duplicate gateway id"))

    monkeypatch.setattr(webhooks, "handle_sepay_transfer", lose_the_race)
    resp = await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 50000), headers=AUTH)

    assert resp.status_code == 200 and resp.json() == {"success": True}


@pytest.mark.anyio
async def test_a_transfer_already_confirmed_by_hand_is_linked_not_collected_again(
    session,
    sepay_env,
):
    client, cashier, order_id, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    manager, _ = await staff(session, "MANAGER", "mgr-webhook")
    await client.post(
        f"/api/v1/sales/payments/{pid}/verification",
        json={"MaGiaoDichNganHang": "FT-MANUAL"},
        headers=cashier,
    )
    confirmed = await client.post(
        f"/api/v1/sales/payments/{pid}/confirm-received", json={}, headers=manager
    )
    assert confirmed.status_code == 200, confirmed.text

    resp = await client.post(
        HOOK,
        json={**_body(pid, 50000, sepay_id=555), "referenceCode": "FT-MANUAL"},
        headers=AUTH,
    )
    again = await client.post(
        HOOK,
        json={**_body(pid, 50000, sepay_id=555), "referenceCode": "FT-MANUAL"},
        headers=AUTH,
    )

    assert resp.status_code == 200 and again.status_code == 200
    row = (
        await session.execute(select(PaymentTransaction).where(PaymentTransaction.id == pid))
    ).scalar_one()
    assert row.gateway_transaction_id == "sepay:555"
    assert await _count(session, Invoice) == 1
    exceptions = (
        await session.execute(
            select(func.count()).where(PaymentTransaction.exception_status.is_not(None))
        )
    ).scalar_one()
    assert exceptions == 0


# --- simulator --------------------------------------------------------------------------------


async def _simulated_qr(session):
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "sim-cashier")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1)])
    started = await client.post(f"/api/v1/sales/orders/{order['MaOrder']}/pay/qr", headers=cashier)
    return client, started.json()["MaGiaoDich"], order["MaOrder"]


@pytest.mark.anyio
async def test_a_non_ascii_signature_is_an_authentication_failure_not_a_crash(session):
    client, pid, _ = await _simulated_qr(session)

    resp = await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"MaGiaoDich": pid, "SoTien": 50000, "ChuKy": "chữ-ký-sai"},
    )

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_the_simulator_is_disabled_outside_the_local_environment(session, monkeypatch):
    client, pid, order_id = await _simulated_qr(session)
    from app.modules.sales.payments import sign_payload

    signature = sign_payload(f"{pid}:50000")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "a-real-secret")
    monkeypatch.setenv("JWT_SECRET", "a-real-jwt-secret-that-is-long-enough-0123456789")
    get_settings.cache_clear()

    resp = await client.post(
        "/api/v1/sales/webhooks/payment",
        json={"MaGiaoDich": pid, "SoTien": 50000, "ChuKy": signature},
    )

    assert resp.status_code == 404
    assert await _status(session, pid) == "Chờ xác nhận"


@pytest.mark.anyio
async def test_the_simulator_rejects_unbounded_or_invalid_fields(session):
    client, pid, _ = await _simulated_qr(session)

    for body in (
        {"MaGiaoDich": pid, "SoTien": -5, "ChuKy": "x"},
        {"MaGiaoDich": 0, "SoTien": 5, "ChuKy": "x"},
        {"MaGiaoDich": pid, "SoTien": 5, "ChuKy": "x" * 500},
        {"MaGiaoDich": pid, "SoTien": 10**30, "ChuKy": "x"},
    ):
        resp = await client.post("/api/v1/sales/webhooks/payment", json=body)
        assert resp.status_code == 422, body
    assert await _status(session, pid) == "Chờ xác nhận"
