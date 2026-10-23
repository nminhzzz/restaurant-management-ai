from collections.abc import Iterator
from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.dependencies import Principal, get_current_user, require_roles
from app.core.errors import UnauthenticatedError
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared.roles import Role

manager_only = require_roles(Role.MANAGER)


def _build_app() -> FastAPI:
    """The real application plus one role-guarded probe route."""
    app = create_app()

    @app.get("/manager-only")
    async def manager_only_route(
        user: Annotated[Principal, Depends(manager_only)],
    ) -> dict[str, str]:
        return {"username": user.username}

    return app


@pytest.fixture(scope="module")
def guarded_client() -> Iterator[TestClient]:
    # A context-managed client keeps one event loop for the whole module. Without it each
    # request gets a fresh loop, and the shared engine pool cannot reuse its connections.
    with TestClient(_build_app()) as client:
        yield client


def test_request_without_token_is_rejected(guarded_client: TestClient) -> None:
    response = guarded_client.get("/manager-only")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_a_malformed_token_is_rejected(guarded_client: TestClient) -> None:
    response = guarded_client.get(
        "/manager-only", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_role_outside_the_allow_list_is_forbidden(guarded_client: TestClient, token_for) -> None:
    response = guarded_client.get(
        "/manager-only", headers={"Authorization": f"Bearer {token_for(Role.WAREHOUSE)}"}
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_allowed_role_reaches_the_handler(guarded_client: TestClient, token_for) -> None:
    response = guarded_client.get(
        "/manager-only", headers={"Authorization": f"Bearer {token_for(Role.MANAGER)}"}
    )

    assert response.status_code == 200
    assert response.json() == {"username": "tester"}


def _production_env(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("JWT_SECRET", "production-secret-0123456789abcdef")
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "production-webhook-secret")
    get_settings.cache_clear()


async def _make_user(session, *, role: str, status: str) -> User:
    await seed_reference_data(session)
    user = User(
        username=f"user-{role.lower()}-{status}",
        password_hash=hash_password("pass"),
        full_name="Test",
        role_id=role,
        status=status,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.mark.anyio
async def test_production_token_takes_the_role_from_the_database(session, monkeypatch) -> None:
    _production_env(monkeypatch)
    user = await _make_user(session, role="CASHIER", status="Hoạt động")
    scheme = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=create_access_token(
            str(user.id), {"role": "MANAGER", "username": user.username}
        ),
    )

    principal = await get_current_user(scheme, session)

    assert principal.role == Role.CASHIER
    assert principal.username == user.username


@pytest.mark.anyio
async def test_production_locked_user_is_rejected_even_with_a_valid_token(
    session, monkeypatch
) -> None:
    _production_env(monkeypatch)
    user = await _make_user(session, role="CASHIER", status="Đã khóa")
    scheme = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=create_access_token(
            str(user.id), {"role": "CASHIER", "username": user.username}
        ),
    )

    with pytest.raises(UnauthenticatedError):
        await get_current_user(scheme, session)
