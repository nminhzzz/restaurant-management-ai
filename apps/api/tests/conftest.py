"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.main import app
from app.shared.roles import Role


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def token_for() -> object:
    def _make(role: Role, user_id: int = 1) -> str:
        return create_access_token(str(user_id), {"role": role.value, "username": "tester"})

    return _make
