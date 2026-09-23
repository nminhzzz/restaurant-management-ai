"""Shared pytest fixtures - Phase 0 foundation."""

from collections.abc import AsyncIterator, Callable, Iterator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.modules.ai.models
import app.modules.catalog.models
import app.modules.inventory.models
import app.modules.sales.models
import app.modules.settings.models
import app.shared.audit  # noqa: F401
from app.core.config import get_settings
from app.core.security import create_access_token
from app.main import app as fastapi_app
from app.shared import business_date
from app.shared.base import Base
from app.shared.roles import Role
from tests.helpers import FIXED_NOW


@pytest.fixture(autouse=True)
def freeze_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
def token_for() -> Callable[..., str]:
    def _make(role: Role, user_id: int = 1) -> str:
        return create_access_token(str(user_id), {"role": role.value, "username": "tester"})

    return _make


@pytest.fixture
def manager_token(token_for: Callable[..., str]) -> str:
    return token_for(Role.MANAGER, user_id=1)


@pytest.fixture
def cashier_token(token_for: Callable[..., str]) -> str:
    return token_for(Role.CASHIER, user_id=2)


@pytest.fixture
def warehouse_token(token_for: Callable[..., str]) -> str:
    return token_for(Role.WAREHOUSE, user_id=3)


@pytest_asyncio.fixture
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as sess:
        yield sess
        await sess.rollback()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
def db_session(session: AsyncSession) -> AsyncSession:
    return session


class FakeLlm:
    def __init__(self) -> None:
        self._queue: list[str] = []
        self.calls: int = 0
        self.last_prompt: str | None = None

    def reply(self, sql: str) -> None:
        self._queue = [sql]

    def reply_sequence(self, seq: list[str]) -> None:
        self._queue = list(seq)

    def complete(self, prompt: str) -> str:
        self.calls += 1
        self.last_prompt = prompt
        if not self._queue:
            return "SELECT 1"
        if len(self._queue) == 1:
            return self._queue[0]
        idx = min(self.calls - 1, len(self._queue) - 1)
        return self._queue[idx]


@pytest.fixture
def fake_llm() -> FakeLlm:
    return FakeLlm()


@pytest_asyncio.fixture
async def seed_views(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS NGUYEN_LIEU (MaNguyenLieu INTEGER PRIMARY KEY, TenNguyenLieu TEXT)"
            )
        )
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS `ORDER` (MaOrder INTEGER PRIMARY KEY, BusinessDate TEXT)"
            )
        )
        await conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS HOA_DON (MaHoaDon INTEGER PRIMARY KEY, BusinessDate TEXT)"
            )
        )
        await conn.execute(text("DROP VIEW IF EXISTS vw_ai_quanly"))
        await conn.execute(text("DROP VIEW IF EXISTS vw_ai_thungan"))
        await conn.execute(text("DROP VIEW IF EXISTS vw_ai_kho"))
        await conn.execute(text("CREATE VIEW vw_ai_quanly AS SELECT * FROM NGUYEN_LIEU"))
        await conn.execute(text("CREATE VIEW vw_ai_thungan AS SELECT * FROM `ORDER`"))
        await conn.execute(text("CREATE VIEW vw_ai_kho AS SELECT * FROM NGUYEN_LIEU"))


@pytest.fixture
def mysql_engine_factory() -> Callable[..., AsyncEngine]:
    def _make(url: str | None = None) -> AsyncEngine:
        db_url = url or get_settings().database_url
        return create_async_engine(db_url, future=True)

    return _make


@pytest.fixture
def mysql_session_factory(
    mysql_engine_factory: Callable[..., AsyncEngine],
) -> Callable[..., AsyncIterator[AsyncSession]]:
    def _factory(url: str | None = None) -> AsyncIterator[AsyncSession]:
        eng = mysql_engine_factory(url)

        async def _gen() -> AsyncIterator[AsyncSession]:
            factory = async_sessionmaker(eng, expire_on_commit=False, class_=AsyncSession)
            async with factory() as sess:
                yield sess

        return _gen()

    return _factory
