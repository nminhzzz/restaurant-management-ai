"""Cross-flow regressions from the second operational review."""

from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.core.errors import BusinessRuleError
from app.modules.inventory import service as inventory
from app.modules.sales import orders, payments, reservations
from app.modules.sales.models import Invoice, PaymentException
from app.shared import business_date
from tests.modules.test_sales_holds import _headers, _setup


async def _order(session):
    dish, ingredient, _ = await _setup(session)
    _, user = await _headers(session)
    result = await orders.submit_order(
        session,
        {"order_type": "Mang về", "lines": [{"dish_id": dish.id, "quantity": 1}]},
        actor_id=user.id,
    )
    return result, ingredient, user


@pytest.mark.anyio
async def test_receiving_an_exception_settles_it_with_the_invoice(session):
    result, _, user = await _order(session)
    payment = await payments.start_qr(session, result["order"].id)
    payment.deadline = business_date.now() - timedelta(minutes=1)
    await session.flush()
    await payments.mark_for_reconciliation(session, payment.id, actor_id=user.id)
    await payments.handle_sepay_transfer(
        session,
        {
            "id": "r2-exact",
            "transferType": "in",
            "transferAmount": 50000,
            "content": f"TT{payment.id}",
        },
    )
    with pytest.raises(BusinessRuleError):
        await payments.resolve_reconciliation(
            session, payment.id, "received", actor_id=user.id, received_amount=Decimal(50000)
        )
    exception = (await session.scalars(select(PaymentException))).one()
    await payments.resolve_exception(session, exception.id, outcome="applied", actor_id=user.id)
    exception = (await session.scalars(select(PaymentException))).one()
    assert exception.status == payments.EXCEPTION_APPLIED
    with pytest.raises(BusinessRuleError):
        await payments.resolve_exception(
            session,
            exception.id,
            outcome="refunded",
            actor_id=user.id,
            note="Return money",
            refund_ref="r2-refund",
            refund_amount=Decimal(50000),
        )
    assert await session.scalar(select(Invoice.total)) == Decimal(50000)


@pytest.mark.anyio
async def test_partially_refunded_money_cannot_pay_the_original_full_bill(session):
    result, _, user = await _order(session)
    payment = await payments.start_qr(session, result["order"].id)
    await payments.request_verification(session, payment.id, actor_id=user.id)
    await payments.reopen_payment(session, payment.id, reason="Retry", actor_id=user.id)
    await payments.handle_sepay_transfer(
        session,
        {
            "id": "r2-partial",
            "transferType": "in",
            "transferAmount": 50000,
            "content": f"TT{payment.id}",
        },
    )
    exception = (await session.scalars(select(PaymentException))).one()
    await payments.resolve_exception(
        session,
        exception.id,
        outcome="refunded",
        actor_id=user.id,
        note="First part",
        refund_ref="r2-part",
        refund_amount=Decimal(1000),
    )
    with pytest.raises(BusinessRuleError):
        await payments.resolve_exception(session, exception.id, outcome="applied", actor_id=user.id)
    assert await session.scalar(select(Invoice.id)) is None


@pytest.mark.anyio
@pytest.mark.parametrize("operation", ["cancel_line", "reduce_line", "cancel_order"])
async def test_returning_order_stock_is_blocked_during_stocktake(session, operation):
    result, ingredient, user = await _order(session)
    line = result["lines"][0]
    await orders.update_line(session, result["order"].id, line.id, 2, actor_id=user.id)
    await inventory.create_stocktake(session, user.id)
    before = Decimal(str(ingredient.stock_qty))
    with pytest.raises(BusinessRuleError):
        if operation == "cancel_line":
            await orders.cancel_line(session, line.id, "Cancel", actor_id=user.id)
        elif operation == "reduce_line":
            await orders.update_line(session, result["order"].id, line.id, 1, actor_id=user.id)
        else:
            await orders.cancel_order(session, result["order"].id, "Cancel", actor_id=user.id)
    assert Decimal(str(ingredient.stock_qty)) == before


@pytest.mark.anyio
async def test_expired_hold_cannot_consume_stock_promised_to_another_selection(session):
    dish, ingredient, _ = await _setup(session, stock=1)
    _, user = await _headers(session)
    old = await reservations.create_hold(
        session, user_id=user.id, selection_code=None, table_id=None, dish_id=dish.id, quantity=1
    )
    old.expires_at = business_date.now().replace(tzinfo=None) - timedelta(minutes=1)
    await session.flush()
    active = await reservations.create_hold(
        session, user_id=user.id, selection_code=None, table_id=None, dish_id=dish.id, quantity=1
    )
    with pytest.raises(BusinessRuleError):
        await orders.submit_order(
            session,
            {
                "order_type": "Mang về",
                "lines": [{"dish_id": dish.id, "quantity": 1, "hold_id": old.id}],
            },
            actor_id=user.id,
            confirm_expired=True,
        )
    assert Decimal(str(ingredient.stock_qty)) == Decimal(1)
    assert active.status == reservations.HOLD_ACTIVE


@pytest.mark.anyio
async def test_webhook_failure_does_not_commit_a_successful_payment_without_an_invoice(
    session, monkeypatch
):
    result, _, _user = await _order(session)
    payment = await payments.start_qr(session, result["order"].id)

    async def fail_invoice(*args, **kwargs):
        raise BusinessRuleError("Injected invoice failure")

    monkeypatch.setattr(payments, "_issue_invoice", fail_invoice)
    outcome = await payments.handle_sepay_transfer(
        session,
        {
            "id": "r2-failed-invoice",
            "transferType": "in",
            "transferAmount": 50000,
            "content": f"TT{payment.id}",
        },
    )
    await session.commit()
    await session.refresh(payment)
    await session.refresh(result["order"])
    assert outcome == "unmatched"
    assert payment.status == payments.QR_PENDING
    assert payment.bank_ref is None
    assert result["order"].status == payments.QR_PENDING_ORDER
    assert await session.scalar(select(Invoice.id)) is None
