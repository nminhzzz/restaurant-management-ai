"""Role → read-only database account (NFR-06).

The assistant executes SQL on a dedicated account per role, each granted
`SELECT` on that role's view only. Sharing one read-only account across the
three roles would let a role's query reach another role's data, which is
exactly what the view split exists to prevent.

A blank URL fails closed: there is deliberately no fallback to the application's own
(read-write) database account.
"""

from types import MappingProxyType

from app.core.config import get_settings
from app.shared.roles import Role

ACCOUNT_FIELDS: MappingProxyType[Role, str] = MappingProxyType(
    {
        Role.MANAGER: "ai_readonly_url_manager",
        Role.CASHIER: "ai_readonly_url_cashier",
        Role.WAREHOUSE: "ai_readonly_url_warehouse",
    }
)


class ReadonlyAccountNotConfigured(RuntimeError):
    """The role has no read-only database account configured."""


def readonly_url_for(role: Role) -> str:
    """Connection string of the read-only account belonging to this role."""
    field = ACCOUNT_FIELDS[role]
    url = str(getattr(get_settings(), field)).strip()
    if not url:
        raise ReadonlyAccountNotConfigured(f"{field.upper()} is not set")
    return url
