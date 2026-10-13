"""Mock QR gateway: an HMAC-SHA256 over `"<payment_id>:<amount>"` with PAYMENT_WEBHOOK_SECRET.

Only reachable when ENVIRONMENT=local (see the router); the built-in fallback secret exists for
that environment alone, so a missing secret anywhere else fails closed.
"""

import hashlib
import hmac

from app.core.config import get_settings

LOCAL_FALLBACK_SECRET = "test-secret"


def enabled() -> bool:
    settings = get_settings()
    return settings.environment == "local" and settings.payment_gateway == "simulator"


def _secret() -> str:
    settings = get_settings()
    if settings.payment_webhook_secret:
        return settings.payment_webhook_secret
    if settings.environment == "local":
        return LOCAL_FALLBACK_SECRET
    return ""


def sign(payload: str) -> str:
    return hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify(payload: str, signature: str) -> bool:
    if not _secret():
        return False
    # Bytes, not str: compare_digest raises TypeError on non-ASCII text.
    return hmac.compare_digest(sign(payload).encode(), signature.encode())
