"""Post-commit kitchen print outbox with conservative transport failure handling.

A successful TCP drain means accepted by the transport, never proof of paper output.
Once a write starts, uncertainty requires a human decision rather than an auto retry.
"""

import asyncio
import contextlib
import logging
import unicodedata
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.core.database import get_session_factory
from app.modules.sales.models import KitchenTicket

logger = logging.getLogger(__name__)
PENDING = "Chờ in"
INFLIGHT = "Đang in"
UNKNOWN = "Chưa rõ kết quả"
FAILED = "Thất bại"
SENT = "Đã gửi máy in"


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class SafePrintFailure(Exception):
    """Failure before any bytes were handed to the printer socket."""


class PrintTransport(Protocol):
    async def send(self, content: str) -> None: ...


class TcpEscPosPrinter:
    """Standard raw TCP ESC/POS adapter; no dependency on browser print dialogs."""

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send(self, content: str) -> None:
        # Most installed ESC/POS printers lack a Vietnamese Unicode font. Render
        # explicit ASCII transliteration; never send UTF-8 to an unknown code page.
        normalized = unicodedata.normalize("NFKD", content.replace("đ", "d").replace("Đ", "D"))
        body = normalized.encode("ascii", "ignore")
        # Strip ESC/POS controls from user notes before adding trusted commands.
        body = bytes(c for c in body if c >= 32 or c == 10)
        payload = b"\x1b@" + body + b"\n\n\n\x1dV\x00"
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    self.settings.kitchen_printer_host, self.settings.kitchen_printer_port
                ),
                timeout=self.settings.kitchen_printer_timeout_seconds,
            )
        except (OSError, TimeoutError) as exc:
            raise SafePrintFailure("Không kết nối được máy in.") from exc
        try:
            writer.write(payload)
            await asyncio.wait_for(
                writer.drain(), timeout=self.settings.kitchen_printer_timeout_seconds
            )
        finally:
            writer.close()
            with contextlib.suppress(OSError, TimeoutError):
                await asyncio.wait_for(writer.wait_closed(), timeout=1)


async def dispatch_tick(
    factory: async_sessionmaker[AsyncSession] | None = None,
    settings: Settings | None = None,
    transport: PrintTransport | None = None,
) -> bool:
    """Claim one committed ticket, commit the lease, then perform bounded I/O.

    MySQL SKIP LOCKED supports multiple API workers. An expired lease is UNKNOWN:
    the crashed process may already have sent bytes. A token fences late results.
    """
    settings = settings or get_settings()
    if transport is None and not settings.kitchen_printer_host:
        return False
    factory = factory or get_session_factory()
    transport = transport or TcpEscPosPrinter(settings)
    now = utc_now()
    token = str(uuid4())
    async with factory() as session:
        await session.execute(
            update(KitchenTicket)
            .where(
                KitchenTicket.print_status == INFLIGHT,
                KitchenTicket.print_lease_until <= now,
            )
            .values(
                print_status=UNKNOWN,
                status=UNKNOWN,
                print_lease_token=None,
                print_lease_until=None,
                print_error="Tiến trình in bị gián đoạn; kiểm tra giấy trước khi in lại.",
            )
        )
        ticket = (
            await session.execute(
                select(KitchenTicket)
                .where(
                    KitchenTicket.print_status == PENDING,
                    or_(
                        KitchenTicket.print_next_attempt_at.is_(None),
                        KitchenTicket.print_next_attempt_at <= now,
                    ),
                )
                .order_by(KitchenTicket.id)
                .limit(1)
                .with_for_update(skip_locked=True)
            )
        ).scalar_one_or_none()
        if ticket is None:
            await session.commit()
            return False
        ticket_id, content = ticket.id, ticket.content
        ticket.print_status = ticket.status = INFLIGHT
        ticket.print_lease_token = token
        ticket.print_lease_until = now + timedelta(
            seconds=2 * settings.kitchen_printer_timeout_seconds + 10
        )
        ticket.print_count += 1
        ticket.print_cycle_attempts += 1
        ticket.printed_at = now
        attempts = ticket.print_cycle_attempts
        await session.commit()
    error = None
    next_attempt = None
    try:
        if not content:
            raise SafePrintFailure("Phiếu không có nội dung; cần kiểm tra dữ liệu.")
        await asyncio.wait_for(
            transport.send(content), timeout=2 * settings.kitchen_printer_timeout_seconds + 2
        )
        status = SENT
    except SafePrintFailure as exc:
        error = str(exc)[:500]
        status = PENDING if attempts < settings.kitchen_printer_max_attempts else FAILED
        if status == PENDING:
            next_attempt = utc_now() + timedelta(seconds=settings.kitchen_printer_retry_seconds)
    except Exception:
        status = UNKNOWN
        error = "Không xác định máy in đã nhận lệnh; kiểm tra giấy trước khi in lại."
        logger.warning("Kitchen ticket %s delivery uncertain", ticket_id)
    async with factory() as session:
        await session.execute(
            update(KitchenTicket)
            .where(KitchenTicket.id == ticket_id, KitchenTicket.print_lease_token == token)
            .values(
                print_status=status,
                status=status,
                print_error=error,
                print_next_attempt_at=next_attempt,
                print_lease_until=None,
                print_lease_token=None,
            )
        )
        await session.commit()
    return True


async def print_queue_loop() -> None:
    settings = get_settings()
    if settings.kitchen_printer_poll_seconds <= 0 or not settings.kitchen_printer_host:
        return
    while True:
        try:
            dispatched = await dispatch_tick(settings=settings)
        except Exception:
            logger.exception("Kitchen print queue tick failed")
            dispatched = False
        if not dispatched:
            await asyncio.sleep(settings.kitchen_printer_poll_seconds)
