"""Durable kitchen queue: commit boundary, safe retries and delivery uncertainty."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.modules.sales.models import KitchenTicket
from tests.modules.test_sales_tickets import _headers, _make_client, _setup


async def create_ticket(session):
    dish, table = await _setup(session)
    client = await _make_client(session)
    headers, _ = await _headers(session)
    result = await client.post(
        "/api/v1/sales/orders",
        headers=headers,
        json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
    )
    assert result.status_code == 201
    ticket = (await session.execute(select(KitchenTicket))).scalar_one()
    return client, headers, ticket


class Printer:
    def __init__(self, error=None):
        self.contents = []
        self.error = error

    async def send(self, content):
        self.contents.append(content)
        if self.error:
            raise self.error


@pytest.mark.anyio
async def test_new_ticket_not_claimed_without_printer(session, session_factory):
    from app.modules.sales.printing import dispatch_tick

    _, _, ticket = await create_ticket(session)
    assert ticket.print_count == 0
    assert await dispatch_tick(session_factory, Settings()) is False
    await session.refresh(ticket)
    assert ticket.print_status == "Chờ in"
    assert ticket.print_count == 0


@pytest.mark.anyio
async def test_worker_prints_snapshot_once_and_only_after_commit(session, session_factory):
    from app.modules.sales.printing import dispatch_tick

    _, _, ticket = await create_ticket(session)
    original = ticket.content
    printer = Printer()
    assert await dispatch_tick(session_factory, Settings(), printer) is True
    assert await dispatch_tick(session_factory, Settings(), printer) is False
    await session.refresh(ticket)
    assert printer.contents == [original]
    assert ticket.print_status == "Đã gửi máy in"
    assert ticket.print_count == 1


@pytest.mark.anyio
async def test_safe_connect_failure_bounded_and_manual_retry_unlimited(session, session_factory):
    from app.modules.sales.printing import SafePrintFailure, dispatch_tick

    client, headers, ticket = await create_ticket(session)
    config = Settings(kitchen_printer_max_attempts=2, kitchen_printer_retry_seconds=0)
    printer = Printer(SafePrintFailure("Connection refused"))
    for _ in range(2):
        assert await dispatch_tick(session_factory, config, printer)
    assert not await dispatch_tick(session_factory, config, printer)
    await session.refresh(ticket)
    assert ticket.print_status == "Thất bại"
    assert ticket.print_count == 2
    for _ in range(4):
        response = await client.post(
            f"/api/v1/sales/orders/{ticket.order_id}/tickets/{ticket.id}/reprint",
            headers=headers,
        )
        assert response.status_code == 200
        # Duplicate clicks while pending do not add another job.
        await client.post(
            f"/api/v1/sales/orders/{ticket.order_id}/tickets/{ticket.id}/reprint",
            headers=headers,
        )
        assert await dispatch_tick(session_factory, config, Printer())
        assert not await dispatch_tick(session_factory, config, Printer())
    await session.refresh(ticket)
    assert ticket.print_count == 6


@pytest.mark.anyio
async def test_ambiguous_failure_never_retries_automatically(session, session_factory):
    from app.modules.sales.printing import dispatch_tick

    _, _, ticket = await create_ticket(session)
    printer = Printer(TimeoutError("after write"))
    assert await dispatch_tick(session_factory, Settings(), printer)
    assert not await dispatch_tick(session_factory, Settings(), printer)
    await session.refresh(ticket)
    assert ticket.print_status == "Chưa rõ kết quả"
    assert len(printer.contents) == 1


@pytest.mark.anyio
async def test_expired_claim_is_unknown_and_not_dispatched_again(session, session_factory):
    from app.modules.sales.printing import dispatch_tick

    _, _, ticket = await create_ticket(session)
    ticket.print_status = ticket.status = "Đang in"
    ticket.print_lease_token = "dead-worker"
    ticket.print_lease_until = datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=5)
    await session.commit()
    printer = Printer()
    assert not await dispatch_tick(session_factory, Settings(), printer)
    await session.refresh(ticket)
    assert ticket.print_status == "Chưa rõ kết quả"
    assert printer.contents == []


@pytest.mark.anyio
async def test_browser_cannot_assert_printer_success(session):
    client, headers, ticket = await create_ticket(session)
    response = await client.post(
        f"/api/v1/sales/orders/{ticket.order_id}/tickets/{ticket.id}/print-result",
        headers=headers,
        json={"ok": True},
    )
    assert response.status_code == 422
    await session.refresh(ticket)
    assert ticket.print_count == 0
    assert ticket.print_status == "Chờ in"


@pytest.mark.anyio
async def test_second_worker_and_staff_cannot_requeue_active_delivery(session, session_factory):
    import asyncio

    from app.modules.sales.printing import dispatch_tick

    client, headers, ticket = await create_ticket(session)
    entered, release = asyncio.Event(), asyncio.Event()

    class BlockingPrinter(Printer):
        async def send(self, content):
            self.contents.append(content)
            entered.set()
            await release.wait()

    printer = BlockingPrinter()
    task = asyncio.create_task(dispatch_tick(session_factory, Settings(), printer))
    await entered.wait()
    try:
        assert not await dispatch_tick(session_factory, Settings(), printer)
        response = await client.post(
            f"/api/v1/sales/orders/{ticket.order_id}/tickets/{ticket.id}/reprint",
            headers=headers,
        )
        assert response.status_code == 422
        assert len(printer.contents) == 1
    finally:
        release.set()
        await task


@pytest.mark.anyio
async def test_tcp_adapter_sends_escpos_to_local_simulator():
    import asyncio

    from app.modules.sales.printing import TcpEscPosPrinter

    received = asyncio.get_running_loop().create_future()

    async def capture(reader, writer):
        received.set_result(await reader.read())
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(capture, "127.0.0.1", 0)
    try:
        config = Settings(
            kitchen_printer_host="127.0.0.1",
            kitchen_printer_port=server.sockets[0].getsockname()[1],
        )
        await TcpEscPosPrinter(config).send("Phở bò x2 (không hành)\x1b@")
        payload = await asyncio.wait_for(received, 2)
        assert payload.startswith(b"\x1b@Pho bo x2 (khong hanh)@")
        assert payload.endswith(b"\x1dV\x00")
        assert payload.count(b"\x1b") == 1
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.anyio
async def test_rollback_never_prints_and_lease_is_committed_before_transport(
    session, session_factory
):
    from app.modules.sales.printing import dispatch_tick

    _, _, ticket = await create_ticket(session)

    class InspectingPrinter(Printer):
        async def send(self, content):
            async with session_factory() as independent:
                committed = await independent.get(KitchenTicket, ticket.id)
                assert committed.print_status == "Đang in"
                assert committed.print_lease_token
                assert committed.content == content
            await super().send(content)

    printer = InspectingPrinter()
    assert await dispatch_tick(session_factory, Settings(), printer)
    session.add(KitchenTicket(order_id=ticket.order_id, content="Rolled back dish"))
    await session.flush()
    await session.rollback()
    assert not await dispatch_tick(session_factory, Settings(), printer)
    assert len(printer.contents) == 1
