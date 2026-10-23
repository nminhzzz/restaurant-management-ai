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
