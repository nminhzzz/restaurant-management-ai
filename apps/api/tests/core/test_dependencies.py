from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.dependencies import Principal, require_roles
from app.main import create_app
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


@pytest.fixture
def guarded_client() -> TestClient:
    return TestClient(_build_app())


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


def _db_client(session) -> AsyncClient:
    app = _build_app()

    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_role_outside_the_allow_list_is_forbidden(
    session, seeded_accounts, token_for
) -> None:
    async with _db_client(session) as client:
        response = await client.get(
            "/manager-only", headers={"Authorization": f"Bearer {token_for(Role.WAREHOUSE, 3)}"}
        )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


async def test_allowed_role_reaches_the_handler(session, seeded_accounts, token_for) -> None:
    async with _db_client(session) as client:
        response = await client.get(
            "/manager-only", headers={"Authorization": f"Bearer {token_for(Role.MANAGER, 1)}"}
        )

    assert response.status_code == 200
    assert response.json() == {"username": "quanly"}
