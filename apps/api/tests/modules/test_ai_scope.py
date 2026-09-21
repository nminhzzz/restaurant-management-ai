import pytest

from app.modules.ai.scope import ROLE_VIEWS, views_for
from app.shared.roles import Role


def test_every_role_has_exactly_one_view() -> None:
    assert set(ROLE_VIEWS) == set(Role)


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Role.MANAGER, {"vw_ai_quanly"}),
        (Role.CASHIER, {"vw_ai_thungan"}),
        (Role.WAREHOUSE, {"vw_ai_kho"}),
    ],
)
def test_views_for_returns_the_role_scope(role: Role, expected: set[str]) -> None:
    assert views_for(role) == expected
