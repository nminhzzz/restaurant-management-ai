import pytest

from app.modules.ai.scope import ROLE_VIEWS, views_for
from app.shared.roles import Role


def test_every_role_has_exactly_one_view() -> None:
    assert set(ROLE_VIEWS) == set(Role)


@pytest.mark.parametrize("role", list(Role))
def test_views_for_returns_the_role_topic_scope(role: Role) -> None:
    assert len(views_for(role)) > 1
    assert all(view.startswith(ROLE_VIEWS[role] + "_") for view in views_for(role))
    assert ROLE_VIEWS[role] not in views_for(role)
