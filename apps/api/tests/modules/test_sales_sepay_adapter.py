"""SePay adapter: QR URL, webhook parsing and API-key check (no network)."""

from decimal import Decimal

import httpx
import pytest

from app.core.config import get_settings
from app.modules.sales.gateways import sepay

WEBHOOK = {
    "id": 92704,
    "gateway": "Vietcombank",
    "transactionDate": "2026-09-26 14:02:37",
    "accountNumber": "0123499999",
    "code": None,
    "content": "NGUYEN VAN A chuyen tien TT388",
    "transferType": "in",
    "transferAmount": 340000,
    "accumulated": 19077000,
    "subAccount": None,
    "referenceCode": "MBVCB.3278907687",
    "description": "",
}


def test_the_qr_url_carries_account_bank_amount_and_code():
    url = sepay.qr_image_url(
        account="0123499999", bank="MBBank", amount=Decimal("340000.0000"), code="TT388"
    )
    assert url.startswith("https://qr.sepay.vn/img?")
    assert "acc=0123499999" in url
    assert "bank=MBBank" in url
    assert "amount=340000" in url
    assert "des=TT388" in url


def test_the_payment_code_is_prefix_plus_id():
    assert sepay.payment_code(388, "TT") == "TT388"


def test_the_payment_id_comes_from_code_then_content():
    transfer = sepay.parse_transfer(WEBHOOK)
    assert sepay.payment_id_of(transfer, "TT") == 388
    with_code = sepay.parse_transfer({**WEBHOOK, "code": "TT12", "content": "khong co ma"})
    assert sepay.payment_id_of(with_code, "TT") == 12
    no_code = sepay.parse_transfer({**WEBHOOK, "content": "chuyen tien an trua"})
    assert sepay.payment_id_of(no_code, "TT") is None


def test_parse_reads_amount_direction_and_reference():
    transfer = sepay.parse_transfer(WEBHOOK)
    assert transfer.sepay_id == "92704"
    assert transfer.direction == "in"
    assert transfer.amount == Decimal("340000")
    assert transfer.reference == "MBVCB.3278907687"


def test_parse_refuses_a_body_without_id_or_amount():
    with pytest.raises(ValueError):
        sepay.parse_transfer({"content": "TT1"})


@pytest.mark.parametrize(
    ("header", "ok"),
    [
        ("Apikey secret-key", True),
        ("apikey secret-key", True),
        ("Apikey wrong", False),
        ("Bearer secret-key", False),
        (None, False),
        ("", False),
    ],
)
def test_the_api_key_check(header, ok):
    assert sepay.api_key_matches(header, "secret-key") is ok


def test_an_empty_expected_key_never_matches():
    assert sepay.api_key_matches("Apikey ", "") is False


def test_selecting_sepay_without_credentials_fails_at_startup(monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="SEPAY"):
        get_settings()


@pytest.mark.anyio
async def test_recent_transfers_reads_the_listing(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer tok"
        assert request.url.params["account_number"] == "0123499999"
        return httpx.Response(
            200,
            json={
                "status": 200,
                "transactions": [
                    {
                        "id": "5",
                        "amount_in": "340000.00",
                        "amount_out": "0.00",
                        "transaction_content": "TT388",
                        "reference_number": "FT1",
                        "code": "TT388",
                    }
                ],
            },
        )

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    rows = await sepay.recent_transfers(
        api_url="https://my.sepay.vn/userapi", token="tok", account="0123499999"
    )

    body = sepay.transfer_from_listing(rows[0])
    assert body == {
        "id": "5",
        "transferType": "in",
        "transferAmount": "340000.00",
        "code": "TT388",
        "content": "TT388",
        "referenceCode": "FT1",
    }
