from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

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
