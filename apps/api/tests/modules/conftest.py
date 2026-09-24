"""Fixtures for settings module."""

import pytest_asyncio

from app.core.security import hash_password
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data


@pytest_asyncio.fixture
async def active_user(session):
    await seed_reference_data(session)
    # create active cashier
    user = User(
        username="thungan01",
        password_hash=hash_password("mat-khau-dung"),
        full_name="Thu Ngan 01",
        role_id="CASHIER",
        status="Ho\u1ea1t \u0111\u1ed9ng",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


@pytest_asyncio.fixture
async def locked_user(session):
    await seed_reference_data(session)
    user = User(
        username="thungan01",
        password_hash=hash_password("mat-khau-dung"),
        full_name="Thu Ngan 01",
        role_id="CASHIER",
        status="\u0110\u00e3 kh\u00f3a",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user
