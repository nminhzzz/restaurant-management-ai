"""NFR-19 / FR-SET-01: the account is re-read on every request.

A token only proves who the caller is; whether the account is still usable, and
which role it holds, is decided by the database at request time.
"""

import jwt
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data

MANAGER_ONLY = "/api/v1/settings/config"


async def _user(session, username: str, role: str, status: str = "Hoạt động") -> User:
    await seed_reference_data(session)
    user = User(
        username=username,
        password_hash=hash_password("pass123"),
        full_name=username,
        role_id=role,
        status=status,
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


def _bearer(user_id: int, **claims: object) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(user_id), claims)}"}


@pytest.mark.anyio
async def test_a_locked_account_loses_access_with_a_token_issued_earlier(api_client, session):
    manager = await _user(session, "ql01", "MANAGER")
    headers = _bearer(manager.id)
    async with api_client as client:
        assert (await client.get(MANAGER_ONLY, headers=headers)).status_code == 200

        manager.status = "Đã khóa"
        await session.commit()
        response = await client.get(MANAGER_ONLY, headers=headers)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


@pytest.mark.anyio
async def test_a_demoted_account_is_authorised_by_its_current_role(api_client, session):
    user = await _user(session, "ql02", "MANAGER")
    headers = _bearer(user.id, role="MANAGER")
    async with api_client as client:
        assert (await client.get(MANAGER_ONLY, headers=headers)).status_code == 200

        user.role_id = "CASHIER"
        await session.commit()
        response = await client.get(MANAGER_ONLY, headers=headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.anyio
async def test_a_forged_role_claim_cannot_raise_privileges(api_client, session):
    cashier = await _user(session, "tn01", "CASHIER")
    headers = _bearer(cashier.id, role="MANAGER", username="ql01")
    async with api_client as client:
        response = await client.get(MANAGER_ONLY, headers=headers)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_a_deleted_account_is_rejected(api_client, session):
    user = await _user(session, "tn02", "CASHIER")
    headers = _bearer(user.id)
    await session.delete(user)
    await session.commit()
    async with api_client as client:
        response = await client.get("/api/v1/settings/auth/me", headers=headers)

    assert response.status_code == 401


@pytest.mark.anyio
async def test_a_token_for_an_unknown_subject_is_rejected(api_client, session):
    await seed_reference_data(session)
    async with api_client as client:
        response = await client.get("/api/v1/settings/auth/me", headers=_bearer(987654))

    assert response.status_code == 401


@pytest.mark.anyio
async def test_a_token_signed_with_another_secret_is_rejected(api_client, session):
    manager = await _user(session, "ql03", "MANAGER")
    forged = jwt.encode(
        {"sub": str(manager.id), "role": "MANAGER"}, "not-the-secret-0123456789abcdef", "HS256"
    )
    async with api_client as client:
        response = await client.get(MANAGER_ONLY, headers={"Authorization": f"Bearer {forged}"})

    assert response.status_code == 401


@pytest.mark.anyio
async def test_login_tokens_carry_no_role_claim(api_client, session):
    await _user(session, "ql04", "MANAGER")
    async with api_client as client:
        response = await client.post(
            "/api/v1/settings/auth/login", json={"username": "ql04", "password": "pass123"}
        )

    claims = jwt.decode(
        response.json()["access_token"],
        get_settings().jwt_secret,
        algorithms=[get_settings().jwt_algorithm],
    )
    assert set(claims) == {"sub", "iat", "exp"}
    assert response.json()["role"] == "MANAGER"


@pytest.mark.anyio
async def test_a_reactivated_account_regains_access_without_a_new_token(api_client, session):
    user = await _user(session, "ql05", "MANAGER", status="Đã khóa")
    headers = _bearer(user.id)
    async with api_client as client:
        assert (await client.get(MANAGER_ONLY, headers=headers)).status_code == 401
        refreshed = (await session.execute(select(User).where(User.id == user.id))).scalar_one()
        refreshed.status = "Hoạt động"
        await session.commit()
        assert (await client.get(MANAGER_ONLY, headers=headers)).status_code == 200
