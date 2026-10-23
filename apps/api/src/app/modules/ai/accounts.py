"""Role → read-only database account (NFR-06).

The assistant executes SQL on a dedicated account per role, each granted
`SELECT` on that role's view only. Sharing one read-only account across the
three roles would let a role's query reach another role's data, which is
exactly what the view split exists to prevent.
"""

from types import MappingProxyType

from sqlalchemy.engine import make_url

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
    """Require a dedicated principal in every environment, including local."""
    settings = get_settings()
    field = ACCOUNT_FIELDS[role]
    url = str(getattr(settings, field))
    if not url:
        raise RuntimeError(f"{field.upper()} must be configured with a dedicated readonly account")
    parsed = make_url(url)
    identity = (parsed.host, parsed.port, parsed.username)
    others = [settings.database_url] + [
        str(getattr(settings, name)) for other, name in ACCOUNT_FIELDS.items() if other != role
    ]
    for other_url in others:
        if other_url:
            other = make_url(other_url)
            if identity == (other.host, other.port, other.username):
                raise RuntimeError("AI readonly accounts must use distinct database principals")
    return url
