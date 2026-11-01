"""Explicit topic-view sets per role; legacy union views are never authorized."""

from types import MappingProxyType

from app.shared.roles import Role

# Stable family labels retained in history and response metadata.
ROLE_VIEWS: MappingProxyType[Role, str] = MappingProxyType(
    {
        Role.MANAGER: "vw_ai_quanly",
        Role.CASHIER: "vw_ai_thungan",
        Role.WAREHOUSE: "vw_ai_kho",
    }
)
ROLE_TOPICS: MappingProxyType[Role, tuple[str, ...]] = MappingProxyType(
    {
        Role.MANAGER: (
            "order",
            "dongmon",
            "hoadon",
            "thanhtoan",
            "ton",
            "giavon",
            "giaodich",
            "nhap",
            "xuat",
            "kiemke",
            "lo",
            "suat",
            "mon",
            "ban",
            "nguyenlieu",
            "nhacungcap",
            "congthuc",
        ),
        Role.CASHIER: ("order", "dongmon", "hoadon", "thanhtoan", "mon", "ban"),
        Role.WAREHOUSE: ("ton", "giaodich", "lo", "nhap", "xuat", "kiemke", "suat", "nguyenlieu"),
    }
)


def views_for(role: Role) -> frozenset[str]:
    return frozenset(f"{ROLE_VIEWS[role]}_{topic}" for topic in ROLE_TOPICS[role])


def views_used(sql: str | None, role: Role) -> list[str]:
    """The topic views a generated query really reads (PhamViDuLieu, document 04 F.29)."""
    if not sql:
        return []
    import sqlglot
    from sqlglot import exp
    from sqlglot.errors import SqlglotError

    try:
        tree = sqlglot.parse_one(sql, read="mysql")
    except SqlglotError:
        return []
    allowed = views_for(role)
    names = {table.name.lower() for table in tree.find_all(exp.Table)}
    return sorted(names & allowed)
