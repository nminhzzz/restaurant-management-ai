"""NFR-06: each role executes on its own read-only account."""

import pytest

from app.core.config import get_settings
from app.modules.ai.accounts import ACCOUNT_FIELDS, readonly_url_for
from app.shared.roles import Role


def test_every_role_has_its_own_account_field() -> None:
    assert set(ACCOUNT_FIELDS) == set(Role)
    assert len(set(ACCOUNT_FIELDS.values())) == len(Role)


@pytest.mark.parametrize(
    ("role", "field"),
    [
        (Role.MANAGER, "ai_readonly_url_manager"),
        (Role.CASHIER, "ai_readonly_url_cashier"),
        (Role.WAREHOUSE, "ai_readonly_url_warehouse"),
    ],
)
def test_readonly_url_reads_the_role_field(role: Role, field: str, monkeypatch) -> None:
    url = f"mysql+asyncmy://{field}@db/restaurant"
    monkeypatch.setenv(field.upper(), url)
    get_settings.cache_clear()

    assert readonly_url_for(role) == url


def test_local_blank_url_is_rejected() -> None:
    """Local development must preserve the same privilege boundary."""
    with pytest.raises(RuntimeError, match="AI_READONLY_URL_MANAGER"):
        readonly_url_for(Role.MANAGER)


def test_non_local_blank_url_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "production-secret-0123456789")
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "production-webhook-secret")
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="AI_READONLY_URL_MANAGER"):
        readonly_url_for(Role.MANAGER)


def test_roles_do_not_share_a_connection_string(monkeypatch) -> None:
    for role in Role:
        monkeypatch.setenv(ACCOUNT_FIELDS[role].upper(), f"mysql+asyncmy://{role.value}@db/r")
    get_settings.cache_clear()

    configured = {readonly_url_for(role) for role in Role}

    assert len(configured) == len(Role)


def test_accounts_cannot_share_the_main_write_user_or_each_other(monkeypatch):
    for role in Role:
        monkeypatch.setenv(ACCOUNT_FIELDS[role].upper(), "mysql+asyncmy://same:secret@db/r")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="distinct"):
        readonly_url_for(Role.CASHIER)
