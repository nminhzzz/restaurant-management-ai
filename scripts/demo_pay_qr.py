"""Demo only: play the bank and confirm the newest pending QR payment.

With PAYMENT_GATEWAY=simulator nothing ever calls the webhook, so a live demo needs a
stand-in for the bank. This signs the confirmation with PAYMENT_WEBHOOK_SECRET exactly
as the simulator gateway verifies it and posts it to the running API:

    cd apps/api && uv run python ../../scripts/demo_pay_qr.py
    cd apps/api && uv run python ../../scripts/demo_pay_qr.py --payment-id 41

The API refuses this webhook when PAYMENT_GATEWAY=sepay, so it cannot fake a real payment.
"""

# ruff: noqa: E402 - application imports follow the path bootstrap.

import argparse
import asyncio
import sys
from decimal import Decimal
from pathlib import Path

for extra in (
    Path(__file__).resolve().parents[1],
    Path(__file__).resolve().parents[1] / "apps" / "api" / "src",
):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

import httpx
from sqlalchemy import select

from app.core.database import get_session_factory
from app.modules.sales.gateways import simulator
from app.modules.sales.models import PaymentTransaction
from app.modules.sales.payments import QR_PENDING


def webhook_body(payment_id: int, amount: Decimal) -> dict[str, object]:
    shown = format(amount.normalize(), "f")
    return {
        "payment_id": payment_id,
        "amount": shown,
        "signature": simulator.sign(f"{payment_id}:{shown}"),
    }


async def pending_payment(payment_id: int | None) -> PaymentTransaction:
    query = select(PaymentTransaction).where(
        PaymentTransaction.method == "QR", PaymentTransaction.status == QR_PENDING
    )
    if payment_id is not None:
        query = query.where(PaymentTransaction.id == payment_id)
    async with get_session_factory()() as session:
        payment = (
            await session.execute(query.order_by(PaymentTransaction.id.desc()).limit(1))
        ).scalar_one_or_none()
    if payment is None:
        raise SystemExit("Không có giao dịch QR nào đang chờ xác nhận.")
    return payment


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payment-id", type=int)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    payment = asyncio.run(pending_payment(args.payment_id))
    response = httpx.post(
        f"{args.base_url}/api/v1/sales/webhooks/payment",
        json=webhook_body(payment.id, payment.amount),
        timeout=10,
    )
    print(f"Giao dịch {payment.id} ({payment.amount:,.0f} ₫): HTTP {response.status_code}")
    response.raise_for_status()


if __name__ == "__main__":
    main()
