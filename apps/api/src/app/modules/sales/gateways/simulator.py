"""Mock QR gateway: an HMAC-SHA256 over `"<payment_id>:<amount>"` with PAYMENT_WEBHOOK_SECRET."""

import hashlib
import hmac

from app.core.config import get_settings


def _secret() -> str:
    return get_settings().payment_webhook_secret or "test-secret"


def sign(payload: str) -> str:
    return hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify(payload: str, signature: str) -> bool:
    return hmac.compare_digest(sign(payload), signature)
