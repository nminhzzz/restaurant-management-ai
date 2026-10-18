"""Physical occupancy is separate from an order's financial lifecycle."""

import pytest

from tests.modules.test_sales_payments import _headers, _make_client, _setup, _submit


@pytest.mark.anyio
async def test_paid_order_keeps_its_table_until_explicit_release(session):
    dish, table = await _setup(session)
    async with await _make_client(session) as client:
        headers, _ = await _headers(session)
        oid = await _submit(session, client, headers, dish, table)
        paid = await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=headers)
        assert paid.status_code == 200
        floor = (await client.get("/api/v1/sales/floor", headers=headers)).json()
        row = next(t for t in floor["tables"] if t["MaBan"] == table.id)
        assert row["TrangThai"] == "Đang phục vụ"
        assert row["order"]["MaOrder"] == oid
        released = await client.post(
            f"/api/v1/sales/tables/{table.id}/release",
            json={"order_id": oid},
            headers=headers,
        )
        assert released.status_code == 200, released.text
        floor = (await client.get("/api/v1/sales/floor", headers=headers)).json()
        row = next(t for t in floor["tables"] if t["MaBan"] == table.id)
        assert row["TrangThai"] == "Trống"
        assert row["order"] is None


@pytest.mark.anyio
async def test_occupied_table_rejects_a_second_order(session):
    dish, table = await _setup(session)
    async with await _make_client(session) as client:
        headers, _ = await _headers(session)
        await _submit(session, client, headers, dish, table)
        response = await client.post(
            "/api/v1/sales/orders",
            json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
            headers=headers,
        )
        assert response.status_code == 422


@pytest.mark.anyio
async def test_a_stale_release_cannot_free_a_new_customers_table(session):
    dish, table = await _setup(session)
    async with await _make_client(session) as client:
        headers, _ = await _headers(session)
        first = await _submit(session, client, headers, dish, table)
        response = await client.post(
            f"/api/v1/sales/tables/{table.id}/release",
            json={"order_id": first},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        second = await _submit(session, client, headers, dish, table)
        stale = await client.post(
            f"/api/v1/sales/tables/{table.id}/release",
            json={"order_id": first},
            headers=headers,
        )
        assert stale.status_code == 422
        # A late payment on the first order also must not free the second table.
        paid = await client.post(f"/api/v1/sales/orders/{first}/pay/cash", headers=headers)
        assert paid.status_code == 200, paid.text
        floor = (await client.get("/api/v1/sales/floor", headers=headers)).json()
        row = next(t for t in floor["tables"] if t["MaBan"] == table.id)
        assert row["TrangThai"] == "Đang phục vụ"
        assert row["order"]["MaOrder"] == second


@pytest.mark.anyio
async def test_warehouse_cannot_release_a_table(session):
    _, table = await _setup(session)
    async with await _make_client(session) as client:
        headers, _ = await _headers(session, role="WAREHOUSE", username="warehouse_release")
        response = await client.post(
            f"/api/v1/sales/tables/{table.id}/release", json={"order_id": None}, headers=headers
        )
        assert response.status_code == 403


@pytest.mark.anyio
async def test_released_table_can_be_deleted_with_an_unpaid_historical_order(session):
    dish, table = await _setup(session)
    async with await _make_client(session) as client:
        headers, _ = await _headers(session, role="MANAGER", username="release_manager")
        oid = await _submit(session, client, headers, dish, table)
        released = await client.post(
            f"/api/v1/sales/tables/{table.id}/release", json={"order_id": oid}, headers=headers
        )
        assert released.status_code == 200
        deleted = await client.delete(f"/api/v1/catalog/tables/{table.id}", headers=headers)
        assert deleted.status_code == 204, deleted.text
