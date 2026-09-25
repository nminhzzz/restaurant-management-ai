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


def _require_resources_for_integration() -> None:
    """Skip integration tests gracefully if host is under pressure.

    Prevents occupying RAM/CPU when MySQL or system is constrained.
    Called from mysql_* fixtures; lightweight gates with no extra deps.
    """
    import os
    import shutil

    # Disk: need at least 2GB free for MySQL data + tmp
    try:
        free = shutil.disk_usage(".").free
        if free < 2 * 1024**3:
            import pytest

            pytest.skip(f"disk free {free // 1024**2}MB < 2048MB — skipping MySQL integration")
    except Exception:
        pass
    # Load: skip if 1-min load > 0.9 * ncpu (machine is saturated)
    try:
        ncpu = os.cpu_count() or 4
        load1 = os.getloadavg()[0]
        if load1 > 0.9 * ncpu:
            import pytest

            pytest.skip(f"load {load1:.1f} > 0.9*{ncpu} — host saturated, skipping integration")
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    """Ensure get_settings() lru_cache does not leak across tests with different ENV."""
    try:
        from app.core.config import get_settings as _gs

        _gs.cache_clear()
    except Exception:
        pass
    yield
    try:
        from app.core.config import get_settings as _gs2

        _gs2.cache_clear()
    except Exception:
        pass


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
        # The A/B/C harness swaps the model per configuration; record what it was told.
        self.model: str | None = None
        self.last_model: str | None = None

    def reply(self, sql: str) -> None:
        self._queue = [sql]

    def reply_sequence(self, seq: list[str]) -> None:
        self._queue = list(seq)

    def complete(self, prompt: str) -> str:
        self.calls += 1
        self.last_prompt = prompt
        self.last_model = self.model
        if not self._queue:
            return "SELECT 1"
        if len(self._queue) == 1:
            return self._queue[0]
        idx = min(self.calls - 1, len(self._queue) - 1)
        return self._queue[idx]


@pytest.fixture
def fake_llm() -> Iterator[FakeLlm]:
    from app.modules.ai import llm
    from app.modules.ai.pipeline import generator

    fake = FakeLlm()
    llm.set_client(fake)
    generator.reset_state()
    yield fake
    llm.set_client(None)
    generator.reset_state()


class _FakeResult:
    def __init__(self, factory) -> None:
        self._factory = factory

    def keys(self) -> list[str]:
        return list(self._factory.columns)

    def fetchall(self) -> list[tuple]:
        return list(self._factory.rows)


class _FakeConnection:
    def __init__(self, factory) -> None:
        self._factory = factory

    async def execute(self, statement):
        self._factory.executed.append(str(statement))
        if self._factory.error is not None:
            raise self._factory.error
        return _FakeResult(self._factory)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeEngine:
    def __init__(self, factory, url) -> None:
        self._factory = factory
        self._url = url

    def connect(self):
        return _FakeConnection(self._factory)

    async def dispose(self) -> None:
        self._factory.disposed += 1


class FakeEngineFactory:
    """Records which read-only URL each role opened, and what ran on it (NFR-06)."""

    def __init__(self) -> None:
        self.urls: list[str] = []
        self.executed: list[str] = []
        self.rows: list[tuple] = []
        self.columns: list[str] = ["MaNguyenLieu", "TenNguyenLieu"]
        self.disposed = 0
        self.error: Exception | None = None

    def __call__(self, url: str) -> _FakeEngine:
        self.urls.append(url)
        return _FakeEngine(self, url)


@pytest.fixture
def fake_engine_factory(monkeypatch) -> FakeEngineFactory:
    """Replace the assistant's engine factory, shared by the module and eval suites."""
    from app.modules.ai.pipeline import executor

    factory = FakeEngineFactory()
    monkeypatch.setattr(executor, "_create_engine", factory)
    return factory


# NOTE: seed_views mirrors `db/views/*.sql` on SQLite (column names/positions only,
# not the MySQL-specific expressions such as CAST or DATE_ADD). The MySQL DDL is
# authoritative; this fixture only needs the same column shape so the prompt tests
# can read it — actual query execution in tests goes through the fake AI engine.
_QUANLY_COLUMNS = [
    "LoaiBanGhi",
    "MaOrder",
    "BusinessDate",
    "LoaiDon",
    "TrangThaiOrder",
    "MaBan",
    "LyDoHuyOrder",
    "MaHoaDon",
    "ThoiDiemXuat",
    "TongTien",
    "MaGiaoDich",
    "PhuongThuc",
    "SoTien",
    "TenMon",
    "TenNhom",
    "SoLuongMon",
    "DonGiaMon",
    "ThanhTienMon",
    "MaNguyenLieu",
    "TenNguyenLieu",
    "DonViTinh",
    "SoLuongTon",
    "MucTonToiThieu",
    "Thang",
    "GiaBinhQuanThang",
    "TongSoLuongNhapThang",
    "MaGiaoDichKho",
    "SoLuong",
    "LoaiGiaoDich",
    "MaPhieuNhap",
    "TenNhaCungCap",
    "DonGiaNhap",
    "SoLuongNhap",
]
_THUNGAN_COLUMNS = [
    "LoaiBanGhi",
    "MaOrder",
    "BusinessDate",
    "LoaiDon",
    "TrangThaiOrder",
    "MaBan",
    "MaHoaDon",
    "ThoiDiemXuat",
    "TongTien",
    "MaGiaoDich",
    "PhuongThuc",
    "SoTien",
    "TenMon",
    "TenNhom",
    "SoLuongMon",
    "DonGiaMon",
    "ThanhTienMon",
]
_KHO_COLUMNS = [
    "LoaiBanGhi",
    "MaNguyenLieu",
    "TenNguyenLieu",
    "DonViTinh",
    "SoLuongTon",
    "MucTonToiThieu",
    "CanhBaoTonThap",
    "MaGiaoDichKho",
    "BusinessDate",
    "SoLuong",
    "LoaiGiaoDich",
    "MaLo",
    "SoLuongConLai",
    "TrangThaiLo",
    "NgayNhapLo",
    "HanSuDungLo",
]


def _branch(columns: list[str], values: dict[str, str]) -> str:
    """Build a SELECT list matching `columns`, NULL-padded except for `values`."""
    return ", ".join(values.get(col, "NULL") for col in columns)


@pytest_asyncio.fixture
async def seed_views(engine: AsyncEngine) -> None:
    quanly_order = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'ORDER'",
            "MaOrder": "o.MaOrder",
            "BusinessDate": "o.BusinessDate",
            "LoaiDon": "o.LoaiDon",
            "TrangThaiOrder": "o.TrangThai",
            "MaBan": "o.MaBan",
            "LyDoHuyOrder": "o.LyDoHuy",
        },
    )
    quanly_dong_mon = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'DONG_MON'",
            "MaOrder": "ct.MaOrder",
            "BusinessDate": "o.BusinessDate",
            "TrangThaiOrder": "o.TrangThai",
            "TenMon": "m.TenMon",
            "TenNhom": "ng.TenNhom",
            "SoLuongMon": "ct.SoLuong",
            "DonGiaMon": "ct.DonGia",
            "ThanhTienMon": "ct.SoLuong * ct.DonGia",
        },
    )
    quanly_hoa_don = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'HOA_DON'",
            "MaOrder": "h.MaOrder",
            "BusinessDate": "h.BusinessDate",
            "MaHoaDon": "h.MaHoaDon",
            "ThoiDiemXuat": "h.ThoiDiemXuat",
            "TongTien": "h.TongTien",
        },
    )
    quanly_thanh_toan = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'THANH_TOAN'",
            "MaOrder": "t.MaOrder",
            "BusinessDate": "t.BusinessDate",
            "MaGiaoDich": "t.MaGiaoDich",
            "PhuongThuc": "t.PhuongThuc",
            "SoTien": "t.SoTien",
        },
    )
    quanly_ton_kho = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'TON_KHO'",
            "MaNguyenLieu": "n.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "SoLuongTon": "n.SoLuongTon",
            "MucTonToiThieu": "n.MucTonToiThieu",
        },
    )
    quanly_gia_von = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'GIA_VON_THANG'",
            "MaNguyenLieu": "gv.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "Thang": "gv.Thang",
            "GiaBinhQuanThang": "gv.GiaBinhQuan",
            "TongSoLuongNhapThang": "gv.TongSoLuongNhap",
        },
    )
    quanly_giao_dich_kho = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'GIAO_DICH_KHO'",
            "BusinessDate": "g.BusinessDate",
            "MaNguyenLieu": "g.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "MaGiaoDichKho": "g.MaGiaoDichKho",
            "SoLuong": "g.SoLuong",
            "LoaiGiaoDich": "g.LoaiGiaoDich",
        },
    )
    quanly_phieu_nhap = _branch(
        _QUANLY_COLUMNS,
        {
            "LoaiBanGhi": "'PHIEU_NHAP'",
            "BusinessDate": "pn.NgayNhap",
            "MaNguyenLieu": "ct.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "MaPhieuNhap": "pn.MaPhieuNhap",
            "TenNhaCungCap": "ncc.TenNhaCungCap",
            "DonGiaNhap": "ct.DonGia",
            "SoLuongNhap": "ct.SoLuong",
        },
    )
    thungan_order = _branch(
        _THUNGAN_COLUMNS,
        {
            "LoaiBanGhi": "'ORDER'",
            "MaOrder": "o.MaOrder",
            "BusinessDate": "o.BusinessDate",
            "LoaiDon": "o.LoaiDon",
            "TrangThaiOrder": "o.TrangThai",
            "MaBan": "o.MaBan",
        },
    )
    thungan_dong_mon = _branch(
        _THUNGAN_COLUMNS,
        {
            "LoaiBanGhi": "'DONG_MON'",
            "MaOrder": "ct.MaOrder",
            "BusinessDate": "o.BusinessDate",
            "TrangThaiOrder": "o.TrangThai",
            "TenMon": "m.TenMon",
            "TenNhom": "ng.TenNhom",
            "SoLuongMon": "ct.SoLuong",
            "DonGiaMon": "ct.DonGia",
            "ThanhTienMon": "ct.SoLuong * ct.DonGia",
        },
    )
    thungan_hoa_don = _branch(
        _THUNGAN_COLUMNS,
        {
            "LoaiBanGhi": "'HOA_DON'",
            "MaOrder": "h.MaOrder",
            "BusinessDate": "h.BusinessDate",
            "MaHoaDon": "h.MaHoaDon",
            "ThoiDiemXuat": "h.ThoiDiemXuat",
            "TongTien": "h.TongTien",
        },
    )
    thungan_thanh_toan = _branch(
        _THUNGAN_COLUMNS,
        {
            "LoaiBanGhi": "'THANH_TOAN'",
            "MaOrder": "t.MaOrder",
            "BusinessDate": "t.BusinessDate",
            "MaGiaoDich": "t.MaGiaoDich",
            "PhuongThuc": "t.PhuongThuc",
            "SoTien": "t.SoTien",
        },
    )
    kho_ton_kho = _branch(
        _KHO_COLUMNS,
        {
            "LoaiBanGhi": "'TON_KHO'",
            "MaNguyenLieu": "n.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "SoLuongTon": "n.SoLuongTon",
            "MucTonToiThieu": "n.MucTonToiThieu",
            "CanhBaoTonThap": "CASE WHEN n.SoLuongTon < n.MucTonToiThieu THEN 1 ELSE 0 END",
        },
    )
    kho_giao_dich_kho = _branch(
        _KHO_COLUMNS,
        {
            "LoaiBanGhi": "'GIAO_DICH_KHO'",
            "MaNguyenLieu": "g.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "MaGiaoDichKho": "g.MaGiaoDichKho",
            "BusinessDate": "g.BusinessDate",
            "SoLuong": "g.SoLuong",
            "LoaiGiaoDich": "g.LoaiGiaoDich",
        },
    )
    kho_lo = _branch(
        _KHO_COLUMNS,
        {
            "LoaiBanGhi": "'LO_NGUYEN_LIEU'",
            "MaNguyenLieu": "l.MaNguyenLieu",
            "TenNguyenLieu": "n.TenNguyenLieu",
            "DonViTinh": "n.DonViTinh",
            "MaLo": "l.MaLo",
            "SoLuongConLai": "l.SoLuongConLai",
            "TrangThaiLo": "l.TrangThai",
            "NgayNhapLo": "l.NgayNhap",
        },
    )
    async with engine.begin() as conn:
        await conn.execute(text("DROP VIEW IF EXISTS vw_ai_quanly"))
        await conn.execute(text("DROP VIEW IF EXISTS vw_ai_thungan"))
        await conn.execute(text("DROP VIEW IF EXISTS vw_ai_kho"))
        await conn.execute(
            text(
                f"CREATE VIEW vw_ai_quanly ({', '.join(_QUANLY_COLUMNS)}) AS "
                f"SELECT {quanly_order} FROM `ORDER` o "
                f"UNION ALL SELECT {quanly_dong_mon} FROM CHI_TIET_ORDER ct "
                "JOIN `ORDER` o ON o.MaOrder = ct.MaOrder "
                "JOIN MON_AN m ON m.MaMon = ct.MaMon "
                "LEFT JOIN NHOM_MON ng ON ng.MaNhomMon = m.MaNhomMon "
                f"UNION ALL SELECT {quanly_hoa_don} FROM HOA_DON h "
                f"UNION ALL SELECT {quanly_thanh_toan} FROM GIAO_DICH_THANH_TOAN t "
                f"UNION ALL SELECT {quanly_ton_kho} FROM NGUYEN_LIEU n "
                f"UNION ALL SELECT {quanly_gia_von} FROM GIA_BINH_QUAN_THANG gv "
                "JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = gv.MaNguyenLieu "
                f"UNION ALL SELECT {quanly_giao_dich_kho} FROM GIAO_DICH_KHO g "
                "JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = g.MaNguyenLieu "
                f"UNION ALL SELECT {quanly_phieu_nhap} FROM CHI_TIET_PHIEU_NHAP ct "
                "JOIN PHIEU_NHAP_KHO pn ON pn.MaPhieuNhap = ct.MaPhieuNhap "
                "JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = ct.MaNguyenLieu "
                "LEFT JOIN NHA_CUNG_CAP ncc ON ncc.MaNhaCungCap = pn.MaNhaCungCap"
            )
        )
        await conn.execute(
            text(
                f"CREATE VIEW vw_ai_thungan ({', '.join(_THUNGAN_COLUMNS)}) AS "
                f"SELECT {thungan_order} FROM `ORDER` o "
                f"UNION ALL SELECT {thungan_dong_mon} FROM CHI_TIET_ORDER ct "
                "JOIN `ORDER` o ON o.MaOrder = ct.MaOrder "
                "JOIN MON_AN m ON m.MaMon = ct.MaMon "
                "LEFT JOIN NHOM_MON ng ON ng.MaNhomMon = m.MaNhomMon "
                f"UNION ALL SELECT {thungan_hoa_don} FROM HOA_DON h "
                f"UNION ALL SELECT {thungan_thanh_toan} FROM GIAO_DICH_THANH_TOAN t"
            )
        )
        await conn.execute(
            text(
                f"CREATE VIEW vw_ai_kho ({', '.join(_KHO_COLUMNS)}) AS "
                f"SELECT {kho_ton_kho} FROM NGUYEN_LIEU n "
                f"UNION ALL SELECT {kho_giao_dich_kho} FROM GIAO_DICH_KHO g "
                "JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = g.MaNguyenLieu "
                f"UNION ALL SELECT {kho_lo} FROM LO_NGUYEN_LIEU l "
                "JOIN NGUYEN_LIEU n ON n.MaNguyenLieu = l.MaNguyenLieu"
            )
        )


@pytest.fixture
def mysql_engine_factory() -> Callable[..., AsyncEngine]:
    def _make(url: str | None = None) -> AsyncEngine:
        _require_resources_for_integration()
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
