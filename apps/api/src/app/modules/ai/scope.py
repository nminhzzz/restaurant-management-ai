"""Role → database view mapping (NFR-06, NFR-12).

The assistant never touches the core business tables. Each role gets one
read-only view, granted to a dedicated read-only database account, and the
generator is only ever told about that single view.
"""

from types import MappingProxyType

from app.shared.roles import Role

ROLE_VIEWS: MappingProxyType[Role, str] = MappingProxyType(
    {
        Role.MANAGER: "vw_ai_quanly",
        Role.CASHIER: "vw_ai_thungan",
        Role.WAREHOUSE: "vw_ai_kho",
    }
)


def views_for(role: Role) -> frozenset[str]:
    """The set of views the assistant may read for this role."""
    return frozenset({ROLE_VIEWS[role]})
