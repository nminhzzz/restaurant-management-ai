"""Transactional MySQL acceptance checks for the stock-to-revenue workflow."""

import hashlib
import hmac
import os
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.core.security import hash_password
from app.main import create_app
from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales.models import Invoice
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import FIXED_NOW

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def mysql_workflow_session(mysql_engine_factory, monkeypatch):
    url = os.environ.get("MYSQL_TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set MYSQL_TEST_DATABASE_URL to a migrated, disposable MySQL database")
    database = make_url(url).database or ""
    if not database.startswith(("restaurant_test", "restaurant_acceptance")):
        pytest.fail("MYSQL_TEST_DATABASE_URL must name a restaurant_test/acceptance database")
    engine = mysql_engine_factory(url)
    # The order counter intentionally uses a separately committed connection.
    # Keep that connection on this test engine and its current asyncio loop too.
    from app.core import database as database_module

    monkeypatch.setattr(database_module, "_engine", engine)
    monkeypatch.setattr(database_module, "_counter_engine", None)
    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            try:
                async with AsyncSession(
                    bind=connection,
                    expire_on_commit=False,
                    join_transaction_mode="create_savepoint",
                ) as session:
                    yield session
            finally:
                await transaction.rollback()
    finally:
        await engine.dispose()
        if database_module._counter_engine is not None:
            await database_module._counter_engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["cash", "qr", "sepay"])
async def test_mysql_stock_sale_payment_costing_and_permissions(
    mysql_workflow_session, monkeypatch, method
):
    session = mysql_workflow_session
    monkeypatch.setenv("PAYMENT_GATEWAY", "simulator")
    monkeypatch.setenv("PAYMENT_WEBHOOK_SECRET", "acceptance-only-secret")
    if method == "sepay":
        monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
        monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
        monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
        monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "acceptance-hook-key")
    get_settings.cache_clear()
    await seed_reference_data(session)
    for role in ("MANAGER", "CASHIER", "WAREHOUSE"):
        session.add(
            User(
                username=f"acceptance_{role.lower()}",
                password_hash=hash_password("acceptance-pass"),
                full_name=f"Kiểm thử {role}",
                role_id=role,
                status="Hoạt động",
            )
        )
    await session.commit()
    app = create_app()

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:

        async def post(path, body, headers, status=201):
            response = await client.post(f"/api/v1{path}", json=body, headers=headers)
            assert response.status_code == status, response.text
            return response.json()

        headers = {}
        for role in ("MANAGER", "CASHIER", "WAREHOUSE"):
            token = await post(
                "/settings/auth/login",
                {"username": f"acceptance_{role.lower()}", "password": "acceptance-pass"},
                {},
                200,
            )
            headers[role] = {"Authorization": f"Bearer {token['access_token']}"}
        manager, cashier, warehouse = (headers[r] for r in headers)
        ingredient = await post(
            "/catalog/ingredients",
            {"TenNguyenLieu": "NL kiểm thử MySQL", "DonViTinh": "kg"},
            manager,
        )
        iid = ingredient["MaNguyenLieu"]
        dish = await post(
            "/catalog/dishes", {"TenMon": "Món kiểm thử MySQL", "GiaHienTai": 50000}, manager
        )
        did = dish["MaMon"]
        await post(
            f"/catalog/dishes/{did}/recipes/assign",
            {"items": [{"MaNguyenLieu": iid, "SoLuong": 1}]},
            manager,
        )
        table = await post("/catalog/tables", {"TenBan": "Bàn kiểm thử MySQL"}, manager)
        for price in (1000, 2000):
            await post(
                "/inventory/receipts",
                {"lines": [{"ingredient_id": iid, "quantity": 10, "unit_price": price}]},
                warehouse,
            )
        # A forbidden write must leave inventory untouched.
        await post(
            "/inventory/issues",
            {"reason": "Hao hụt", "lines": [{"ingredient_id": iid, "quantity": 1}]},
            cashier,
            403,
        )
        order = await post(
            "/sales/orders",
            {"MaBan": table["MaBan"], "lines": [{"MaMon": did, "SoLuong": 2}]},
            cashier,
        )
        oid = order["MaOrder"]
        if method == "cash":
            await post(f"/sales/orders/{oid}/pay/cash", {}, cashier, 200)
        else:
            payment = await post(f"/sales/orders/{oid}/pay/qr", {}, cashier)
            pid = payment["MaGiaoDich"]
            if method == "sepay":
                assert payment["payment_code"] == f"TT{pid}"
                assert "amount=100000" in payment["qr_image_url"]
                hook = "/sales/webhooks/sepay"
                auth = {"Authorization": "Apikey acceptance-hook-key"}
                body = {
                    "id": 92704,
                    "transferType": "in",
                    "transferAmount": 100000,
                    "content": f"TT{pid}",
                    "referenceCode": "ACCEPTANCE-92704",
                }
            else:
                signature = hmac.new(
                    b"acceptance-only-secret", f"{pid}:100000".encode(), hashlib.sha256
                ).hexdigest()
                hook, auth = "/sales/webhooks/payment", {}
                body = {"payment_id": pid, "amount": 100000, "signature": signature}
            await post(hook, body, auth, 200)
            await post(hook, body, auth, 200)
        invoices = (
            (await session.execute(select(Invoice).where(Invoice.order_id == oid))).scalars().all()
        )
        assert len(invoices) == 1
        floor = (await client.get("/api/v1/sales/floor", headers=cashier)).json()
        occupied = next(row for row in floor["tables"] if row["MaBan"] == table["MaBan"])
        assert occupied["TrangThai"] == "Đang phục vụ"
        assert occupied["MaOrderDangPhucVu"] == oid
        await post(f"/sales/tables/{table['MaBan']}/release", {"order_id": oid}, cashier, 200)
        floor = (await client.get("/api/v1/sales/floor", headers=cashier)).json()
        freed = next(row for row in floor["tables"] if row["MaBan"] == table["MaBan"])
        assert freed["TrangThai"] == "Trống"
        assert freed["order"] is None
        await post(
            "/inventory/issues",
            {"reason": "Hao hụt", "lines": [{"ingredient_id": iid, "quantity": 3}]},
            warehouse,
        )
        month = FIXED_NOW.year * 100 + FIXED_NOW.month
        await post(f"/inventory/costing/{month}/close", {}, manager, 200)
        response = await client.get(
            "/api/v1/reports/costs", params={"month": "2026-09"}, headers=manager
        )
        assert response.status_code == 200, response.text
        assert Decimal(str(response.json()["HaoHut"])) == 4500
        assert Decimal(str(response.json()["TongGiaVon"])) == 7500
        assert response.json()["TamTinh"] is False
        response = await client.get(
            "/api/v1/reports/margin", params={"month": "2026-09"}, headers=manager
        )
        assert response.status_code == 200, response.text
        assert Decimal(str(response.json()["BienLoiNhuanGop"])) == 92500
        denied = await client.get("/api/v1/reports/revenue", headers=warehouse)
        assert denied.status_code == 403
        await session.refresh(await session.get(Ingredient, iid))
        assert (await session.get(Ingredient, iid)).stock_qty == 15
        lots = (
            (
                await session.execute(
                    select(IngredientLot)
                    .where(IngredientLot.ingredient_id == iid)
                    .order_by(IngredientLot.id)
                )
            )
            .scalars()
            .all()
        )
        assert [lot.quantity_remaining for lot in lots] == [5, 10]
        movements = (
            (await session.execute(select(StockMovement).where(StockMovement.ingredient_id == iid)))
            .scalars()
            .all()
        )
        assert sum(m.qty for m in movements) == 15
