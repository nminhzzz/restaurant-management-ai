"""Catch-up must cover older transfers and stop before a failed transfer."""

import httpx
import pytest
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.errors import BusinessRuleError
from app.modules.sales import payments
from app.modules.sales.gateways import sepay
from app.modules.sales.models import PaymentException
from app.modules.settings.models import SystemConfig
from app.modules.settings.service import seed_reference_data


def _configure(monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_API_TOKEN", "test-token")
    get_settings.cache_clear()


@pytest.mark.anyio
async def test_poll_catches_151_descending_transfers_without_losing_the_oldest(
    session, session_factory, monkeypatch
):
    _configure(monkeypatch)
    await seed_reference_data(session)
    await session.commit()

    def handler(request):
        since = int(request.url.params.get("since_id", "0"))
        limit = int(request.url.params["limit"])
        return httpx.Response(
            200,
            json={
                "transactions": [
                    {"id": str(i), "amount_in": "50000", "transaction_content": "TT99999"}
                    for i in range(1150, 999, -1)
                    if i >= since
                ][:limit]
            },
        )

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    await payments.sync_recent_transfers(factory=session_factory)
    await payments.sync_recent_transfers(factory=session_factory)
    assert await session.scalar(select(func.count()).select_from(PaymentException)) == 151
    config = (await session.scalars(select(SystemConfig))).one()
    await session.refresh(config)
    assert config.sepay_cursor == "1150"


@pytest.mark.anyio
async def test_a_failed_older_transfer_does_not_advance_the_cursor_past_it(
    session, session_factory, monkeypatch
):
    _configure(monkeypatch)
    await seed_reference_data(session)
    await session.commit()

    async def listing(**kwargs):
        return [
            {"id": str(i), "amount_in": "50000", "transaction_content": "TT99999"}
            for i in (102, 101)
        ]

    original = payments.handle_sepay_transfer

    async def fail_older(session, body):
        if body["id"] == "101":
            raise BusinessRuleError("Injected processing failure")
        return await original(session, body)

    monkeypatch.setattr(sepay, "recent_transfers", listing)
    monkeypatch.setattr(payments, "handle_sepay_transfer", fail_older)
    await payments.sync_recent_transfers(factory=session_factory)
    config = (await session.scalars(select(SystemConfig))).one()
    await session.refresh(config)
    assert config.sepay_cursor is None
    assert await session.scalar(select(func.count()).select_from(PaymentException)) == 0


@pytest.mark.anyio
async def test_a_truncated_listing_is_rejected_instead_of_skipping_older_money(monkeypatch):
    def handler(request):
        return httpx.Response(
            200, json={"transactions": [{"id": str(i), "amount_in": "1"} for i in range(5000)]}
        )

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    with pytest.raises(BusinessRuleError):
        await sepay.recent_transfers(api_url="https://test", token="test", account="test")
