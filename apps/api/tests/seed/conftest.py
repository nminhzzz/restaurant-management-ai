"""Fixtures for the seed tests."""

import pytest_asyncio

from app.modules.settings.service import seed_reference_data


@pytest_asyncio.fixture
async def seeded_reference(session):
    """Roles and the singleton config row — every foreign key hangs from these."""
    await seed_reference_data(session)
    await session.commit()
    return session
