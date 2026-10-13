"""NFR-06: each role executes on its own read-only account."""

import pytest

from app.core.config import get_settings
from app.modules.ai.accounts import ACCOUNT_FIELDS, ReadonlyAccountNotConfigured, readonly_url_for
from app.shared.roles import Role


def test_every_role_has_its_own_account_field() -> None:
    assert set(ACCOUNT_FIELDS) == set(Role)
    assert len(set(ACCOUNT_FIELDS.values())) == len(Role)


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Role.MANAGER, "ai_readonly_url_manager"),
        (Role.CASHIER, "ai_readonly_url_cashier"),
        (Role.WAREHOUSE, "ai_readonly_url_warehouse"),
    ],
)
def test_readonly_url_reads_the_role_field(role: Role, expected: str, readonly_urls) -> None:
    settings = get_settings()

    assert readonly_url_for(role) == getattr(settings, expected)


def test_roles_do_not_share_a_connection_string(readonly_urls) -> None:
    settings = get_settings()
    configured = {
        role: readonly_url_for(role)
        for role in Role
        if getattr(settings, ACCOUNT_FIELDS[role]) != ""
    }

    assert len(set(configured.values())) == len(configured)


@pytest.mark.parametrize("role", list(Role))
@pytest.mark.parametrize("blank", ["", "   "])
def test_a_blank_account_url_fails_closed_instead_of_falling_back(
    role: Role, blank: str, monkeypatch
) -> None:
    for field in ACCOUNT_FIELDS.values():
        monkeypatch.setenv(field.upper(), "mysql+asyncmy://ai@db/restaurant")
    monkeypatch.setenv(ACCOUNT_FIELDS[role].upper(), blank)
    get_settings.cache_clear()
    try:
        with pytest.raises(ReadonlyAccountNotConfigured):
            readonly_url_for(role)
    finally:
        get_settings.cache_clear()
