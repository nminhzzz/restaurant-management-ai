"""SePay (VietQR bank transfer) adapter — pure helpers plus one read-only HTTP call.

SePay authenticates webhooks with `Authorization: Apikey <key>`, not a body signature,
so the endpoint must only be exposed over HTTPS.
"""

import hmac
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

import httpx

QR_IMAGE_BASE = "https://qr.sepay.vn/img"

# The webhook is public: every field is bounded before anything is looked up or stored.
MAX_BODY_BYTES = 16 * 1024
_MAX_ID = 64
_MAX_SHORT = 100
_MAX_CONTENT = 1000
_MAX_AMOUNT = Decimal("1000000000000")

# Tests swap this for httpx.MockTransport; production uses the default transport.
_transport: httpx.AsyncBaseTransport | None = None


@dataclass(frozen=True)
class Transfer:
    sepay_id: str
    direction: str
    amount: Decimal
    code: str | None
    content: str
    reference: str | None
    account: str | None = None


def payment_code(payment_id: int, prefix: str) -> str:
    return f"{prefix}{payment_id}"


def qr_image_url(*, account: str, bank: str, amount: Decimal, code: str) -> str:
    query = urlencode({"acc": account, "bank": bank, "amount": str(int(amount)), "des": code})
    return f"{QR_IMAGE_BASE}?{query}"


def api_key_matches(header: str | None, expected: str) -> bool:
    if not expected or not header:
        return False
    scheme, _, key = header.partition(" ")
    return scheme.lower() == "apikey" and hmac.compare_digest(
        key.strip().encode(), expected.encode()
    )


def _bounded(value: Any, limit: int, name: str) -> str | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool | dict | list):
        raise ValueError(f"{name} has an unsupported type")
    text = str(value)
    if len(text) > limit:
        raise ValueError(f"{name} is too long")
    return text


def parse_transfer(body: dict[str, Any]) -> Transfer:
    sepay_id = _bounded(body.get("id"), _MAX_ID, "id")
    raw_amount = body.get("transferAmount")
    if sepay_id is None or raw_amount is None or isinstance(raw_amount, bool | dict | list):
        raise ValueError("SePay payload needs id and transferAmount")
    try:
        amount = Decimal(str(raw_amount))
    except InvalidOperation as exc:
        raise ValueError("transferAmount is not a number") from exc
    if not amount.is_finite() or amount <= 0 or amount > _MAX_AMOUNT:
        raise ValueError("transferAmount is out of range")
    return Transfer(
        sepay_id=sepay_id,
        direction=str(body.get("transferType") or "")[:_MAX_SHORT],
        amount=amount,
        code=_bounded(body.get("code"), _MAX_SHORT, "code"),
        content=_bounded(body.get("content"), _MAX_CONTENT, "content") or "",
        reference=_bounded(body.get("referenceCode"), _MAX_SHORT, "referenceCode"),
        account=_bounded(body.get("accountNumber"), 50, "accountNumber"),
    )


def account_matches(transfer: Transfer, expected: str) -> bool:
    """The money must land on the account this restaurant configured, or it is not ours."""
    return (
        bool(expected)
        and transfer.account is not None
        and hmac.compare_digest(transfer.account.encode(), expected.encode())
    )


def payment_id_of(transfer: Transfer, prefix: str) -> int | None:
    pattern = re.compile(rf"{re.escape(prefix)}(\d+)", re.IGNORECASE)
    for text in (transfer.code or "", transfer.content):
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def transfer_from_listing(item: dict[str, Any]) -> dict[str, Any]:
    amount_in = Decimal(str(item.get("amount_in") or "0"))
    return {
        "id": str(item.get("id")),
        "transferType": "in" if amount_in > 0 else "out",
        "transferAmount": item.get("amount_in"),
        "code": item.get("code"),
        "content": item.get("transaction_content") or "",
        "referenceCode": item.get("reference_number"),
    }


async def recent_transfers(*, api_url: str, token: str, account: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(transport=_transport, timeout=5.0) as client:
        response = await client.get(
            f"{api_url}/transactions/list",
            params={"account_number": account, "limit": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        rows = response.json().get("transactions") or []
    return [row for row in rows if isinstance(row, dict)]
