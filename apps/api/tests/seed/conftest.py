"""Fixtures for the seed tests."""

import pytest_asyncio

from app.modules.settings.service import seed_reference_data


@pytest_asyncio.fixture
async def seeded_reference(session):
    """Roles and the singleton config row — every foreign key hangs from these."""
    await seed_reference_data(session)
    await session.commit()
    return session


@pytest_asyncio.fixture
async def seeded_year(session, seeded_reference):
    """A full year of operations, at a size a test can afford (NFR-03 shape)."""
    from scripts.seed.catalog import seed_catalog
    from scripts.seed.config import SeedConfig
    from scripts.seed.operations import seed_operations

    config = SeedConfig(seed=42, months=12, orders_target=365)
    ids = await seed_catalog(session, config)
    summary = await seed_operations(session, config, ids)
    return summary
