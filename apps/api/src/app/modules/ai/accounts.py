"""Role → read-only database account (NFR-06).

The assistant executes SQL on a dedicated account per role, each granted
`SELECT` on that role's view only. Sharing one read-only account across the
three roles would let a role's query reach another role's data, which is
exactly what the view split exists to prevent.
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


def readonly_url_for(role: Role) -> str:
    """Connection string of the read-only account belonging to this role."""
    return str(getattr(get_settings(), ACCOUNT_FIELDS[role]))
