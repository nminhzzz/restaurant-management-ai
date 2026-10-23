"""Appendix J tooling contracts without network or developer databases."""

import csv
import io
from collections import Counter
from datetime import datetime

import httpx
import pytest
from scripts.perf.load import BusinessUser, Sample, aggregate, write_csv
from scripts.perf.seed import build_plan, seed_dataset
from scripts.perf.verify import snapshot, verify

from app.shared.business_date import now as real_now


def test_exact_reproducible_plan():
    plan = build_plan(20261019, 20000, 12, datetime(2026, 10, 19, 12))
    assert plan == build_plan(20261019, 20000, 12, datetime(2026, 10, 19, 12))
    assert Counter(row.status for row in plan) == {
        "paid": 18000,
        "cancelled": 1000,
        "review": 500,
        "closed": 500,
    }
    assert Counter(row.takeaway for row in plan) == {False: 14000, True: 6000}
    assert all(1 <= len(row.lines) <= 5 for row in plan)
    assert all(1 <= quantity <= 3 for row in plan for _, quantity in row.lines)
    assert len({row.moment.strftime("%Y-%m") for row in plan}) == 12


def test_csv_percentiles_and_errors():
    samples = [
        Sample("run", "now", "CASHIER", "hold", 201, ms, "ok", 5) for ms in [1, 2, 3, 4, 100]
    ]
    samples.append(Sample("run", "now", "CASHIER", "hold", 409, 9, "business_rejection", 5))
    samples.append(Sample("run", "now", "CASHIER", "hold", 403, 10, "technical_error", 5))
    result = aggregate(samples, 10)["hold"]
    assert result["p50_ms"] == 3
    assert result["p95_ms"] == pytest.approx(80.8)
    assert result["success_per_second"] == 0.5
    assert result["technical_errors"] == result["business_rejections"] == 1
    output = io.StringIO()
    write_csv(samples, output)
    assert len(list(csv.DictReader(io.StringIO(output.getvalue())))) == 7


@pytest.mark.asyncio
async def test_dependent_cycle_uses_response_ids_and_roles():
    calls = []
    hold_id = 70

    def handler(request):
        nonlocal hold_id
        calls.append((request.method, request.url.path, request.headers.get("authorization")))
        if request.url.path.endswith("/holds") and request.method == "POST":
            hold_id += 1
            return httpx.Response(201, json={"MaGiuCho": hold_id, "MaLuotChon": "selection"})
        if request.url.path.endswith("/orders") and request.method == "POST":
            return httpx.Response(201, json={"MaOrder": 900 + hold_id, "rejected": []})
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as client:
        user = BusinessUser(
            client,
            {"CASHIER": "c", "MANAGER": "m", "WAREHOUSE": "w"},
            {"dish_id": 4, "catalog_id": 40, "ingredient_id": 30, "supplier_id": 5},
            "run",
            5,
            1,
            pause=False,
        )
        samples = await user.cycle()
    assert Counter(s.operation for s in samples) == {
        "hold": 2,
        "adjust_hold": 2,
        "send": 2,
        "read_order": 1,
        "read_menu": 1,
        "catalog": 1,
        "receipt": 1,
    }
    assert ("PATCH", "/api/v1/sales/holds/71", "Bearer c") in calls
    assert ("GET", "/api/v1/sales/orders/972", "Bearer c") in calls
    assert any(path.endswith("/dishes/40") and token == "Bearer m" for _, path, token in calls)
    assert calls[-1][2] == "Bearer w"


@pytest.mark.asyncio
async def test_missing_hold_dependency_never_sends():
    calls = []

    def handler(request):
        calls.append(request.url.path)
        return httpx.Response(201, json={})

    async with httpx.AsyncClient(
        transport=httpx.MockTransport(handler), base_url="http://test"
    ) as client:
        user = BusinessUser(
            client,
            {"CASHIER": "c", "MANAGER": "m", "WAREHOUSE": "w"},
            {"dish_id": 4, "catalog_id": 40, "ingredient_id": 30, "supplier_id": 5},
            "run",
            5,
            1,
            pause=False,
        )
        samples = await user.cycle()
    assert "/api/v1/sales/orders" not in calls
    assert samples[0].outcome == "technical_error"


@pytest.mark.asyncio
async def test_small_service_seed_manifest_and_lot_ledger(session, monkeypatch):
    monkeypatch.setattr("app.shared.business_date.now", real_now)
    manifest, accounts = await seed_dataset(
        session, seed=12, orders=40, months=2, now=datetime(2026, 10, 19, 12), users=1
    )
    assert manifest["counts"]["orders"] == 40
    assert manifest["statuses"] == {
        "Đã thanh toán": 36,
        "Đã hủy": 2,
        "Chờ xác minh thanh toán": 1,
        "Đóng \u2013 chưa thu được tiền": 1,
    }
    assert manifest["counts"]["dishes"] == 40
    assert manifest["counts"]["ingredients"] == 30
    assert set(accounts[0]) == {"CASHIER", "MANAGER", "WAREHOUSE", "data"}
    assert await verify(session) == []
    assert (await snapshot(session))["checksum"] == manifest["checksum"]


@pytest.mark.asyncio
async def test_real_routes_cycle_and_repeat_send_do_not_consume_twice(session, monkeypatch):
    import json

    from app.core.database import get_session
    from app.main import app

    monkeypatch.setattr("app.shared.business_date.now", real_now)
    _, accounts = await seed_dataset(
        session, seed=19, orders=40, months=2, now=datetime(2026, 10, 19, 12), users=1
    )

    async def override_session():
        yield session

    app.dependency_overrides[get_session] = override_session
    transport = httpx.ASGITransport(app=app)
    sends = []

    async def handle(request):
        if request.url.path == "/api/v1/sales/orders" and request.method == "POST":
            sends.append(json.loads(request.content))
        return await transport.handle_async_request(request)

    try:
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handle), base_url="http://test"
        ) as client:
            tokens = {}
            for role in ("CASHIER", "MANAGER", "WAREHOUSE"):
                response = await client.post("/api/v1/settings/auth/login", json=accounts[0][role])
                assert response.status_code == 200, response.text
                tokens[role] = response.json()["access_token"]
            user = BusinessUser(client, tokens, accounts[0]["data"], "routes", 5, 1, pause=False)
            samples = await user.cycle()
            assert len(samples) == 10
            assert all(sample.outcome == "ok" for sample in samples), samples
            before = await snapshot(session)
            response = await client.post(
                "/api/v1/sales/orders",
                json=sends[-1],
                headers={"Authorization": f"Bearer {tokens['CASHIER']}"},
            )
            assert response.status_code == 201, response.text
            assert (await snapshot(session))["checksum"] == before["checksum"]
            assert await verify(session) == []
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest.mark.parametrize(
    "url", ["mysql+asyncmy://localhost/restaurant", "sqlite+aiosqlite:///:memory:"]
)
def test_database_guard_requires_explicit_dedicated_name(url):
    from scripts.perf.seed import dedicated_database

    with pytest.raises(ValueError, match="perf_"):
        dedicated_database(url)


def test_accounts_must_not_share_role_sessions():
    from scripts.perf.load import validate_accounts

    account = {role: {"username": role} for role in ("CASHIER", "MANAGER", "WAREHOUSE")}
    with pytest.raises(ValueError, match="riêng"):
        validate_accounts([account] * 5, 5)
