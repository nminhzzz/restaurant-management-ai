"""The demo helper must sign a QR confirmation exactly like the bank simulator expects."""

from decimal import Decimal

from scripts.demo_pay_qr import webhook_body

from app.modules.sales.gateways import simulator


def test_the_body_carries_a_valid_simulator_signature() -> None:
    body = webhook_body(41, Decimal("185000.0000"))

    assert body["payment_id"] == 41
    assert body["amount"] == "185000"
    assert simulator.verify("41:185000", body["signature"])


def test_a_fractional_amount_keeps_its_decimals() -> None:
    assert webhook_body(7, Decimal("12500.5000"))["amount"] == "12500.5"
