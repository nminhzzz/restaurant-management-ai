"""Monthly weighted average costing close."""

from datetime import date, datetime

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import Ingredient
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from tests.helpers import FIXED_NOW


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="MANAGER", username="mgr_cost"):
    await seed_reference_data(session)
    from sqlalchemy import select as sel

    r = await session.execute(sel(User).where(User.username == username))
    u = r.scalar_one_or_none()
    if u is None:
        u = User(
            username=username,
            password_hash=hash_password("pass"),
            full_name=username,
            role_id=role,
            status="Hoạt động",
        )
        session.add(u)
        await session.flush()
        await session.commit()
    tok = create_access_token(str(u.id), {"role": u.role_id, "username": u.username})
    return {"Authorization": f"Bearer {tok}"}, u


async def _ingredient(session, name="NL Cost"):
    ing = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=0, is_deleted=False)
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


@pytest.mark.anyio
async def test_close_month_computes_weighted_average(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    # Two receipts in the same (frozen) business month at different unit prices.
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1000}]},
        headers=h,
    )
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 2000}]},
        headers=h,
    )
    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    r = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    row = next(x for x in body if x["MaNguyenLieu"] == ing.id)
    # (10*1000 + 10*2000) / 20 = 1500
    assert row["GiaBinhQuan"] == 1500
    assert row["TongSoLuongNhap"] == 20


@pytest.mark.anyio
async def test_close_month_rejects_invalid_month(session):
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post("/api/v1/inventory/costing/202513/close", headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_close_month_requires_manager(session):
    client = await _make_client(session)
    h, _ = await _headers(session, role="WAREHOUSE", username="kho_cost")
    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    r = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=h)
    assert r.status_code == 403


@pytest.mark.anyio
async def test_closing_a_month_prices_its_write_offs_and_is_audited(session):
    """FR-REP-05b: waste stays at cost 0 ("tạm tính") until the month is closed.

    Closing through the API must also backfill the write-offs, otherwise the
    provisional label on the cost report never clears.
    """
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssue, StockIssueLine
    from app.shared.audit import SystemAuditLog

    ing = await _ingredient(session, "NL hao hụt cần chốt")
    client = await _make_client(session)
    h, manager = await _headers(session)
    await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1500}]},
        headers=h,
    )
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 2}]},
        headers=h,
    )
    assert issued.status_code == 201, issued.text
    issue = (await session.execute(sel(StockIssue))).scalar_one()
    assert issue.issue_date == FIXED_NOW
    issue.created_at = datetime(2026, 8, 31, 23, 0)
    await session.flush()

    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    r = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=h)

    assert r.status_code == 200, r.text
    line = (
        await session.execute(sel(StockIssueLine).where(StockIssueLine.ingredient_id == ing.id))
    ).scalar_one()
    await session.refresh(line)
    assert line.estimated_cost == 3000
    audit = (
        await session.execute(
            sel(SystemAuditLog).where(SystemAuditLog.action == "CLOSE_COSTING_MONTH")
        )
    ).scalar_one()
    assert audit.user_id == manager.id
    assert audit.target_id == str(month)


@pytest.mark.anyio
async def test_closing_a_month_prices_legacy_issue_without_issue_date(session):
    from sqlalchemy import select

    from app.modules.inventory.models import StockIssue, StockIssueLine

    ing = await _ingredient(session, "NL phiếu xuất cũ")
    client = await _make_client(session)
    headers, _ = await _headers(session)
    receipt = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": 10, "unit_price": 1500}]},
        headers=headers,
    )
    assert receipt.status_code == 201, receipt.text
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 2}]},
        headers=headers,
    )
    assert issued.status_code == 201, issued.text
    issue = (await session.execute(select(StockIssue))).scalar_one()
    issue.issue_date = None
    issue.created_at = FIXED_NOW
    await session.flush()

    month = FIXED_NOW.year * 100 + FIXED_NOW.month
    response = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=headers)

    assert response.status_code == 200, response.text
    line = (
        await session.execute(select(StockIssueLine).where(StockIssueLine.issue_id == issue.id))
    ).scalar_one()
    await session.refresh(line)
    assert line.estimated_cost == 3000


# --- FR-REP-05a: the average is weighted by the opening stock and carried forward -------------


async def _receive(client, headers, ing, quantity, price, when):
    response = await client.post(
        "/api/v1/inventory/receipts",
        json={
            "receipt_date": when.isoformat(),
            "lines": [{"ingredient_id": ing.id, "quantity": quantity, "unit_price": price}],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["MaPhieuNhap"]


async def _close(client, headers, month):
    response = await client.post(f"/api/v1/inventory/costing/{month}/close", headers=headers)
    assert response.status_code == 200, response.text
    return {row["MaNguyenLieu"]: row for row in response.json()}


async def _move_consumption_to(session, ing, day):
    """The ledger of the tests is stamped with the frozen clock; place it in another month."""
    from sqlalchemy import update

    from app.modules.inventory.models import StockMovement

    await session.execute(
        update(StockMovement)
        .where(StockMovement.ingredient_id == ing.id, StockMovement.kind != "Nhập")
        .values(business_date=day)
    )
    await session.flush()


AUG = datetime(2026, 8, 10, 9, 0)
SEP = datetime(2026, 9, 5, 9, 0)


@pytest.mark.anyio
async def test_the_average_weights_the_opening_stock_with_the_previous_average(session):
    ing = await _ingredient(session, "NL tồn đầu kỳ")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)
    await _close(client, h, 202608)
    await _receive(client, h, ing, 10, 2000, SEP)

    september = (await _close(client, h, 202609))[ing.id]

    # (10 x 1.000 opening + 10 x 2.000 received) / 20, not the 2.000 of the month's receipts alone.
    assert september["GiaBinhQuan"] == 1500
    assert september["TongSoLuongNhap"] == 10


@pytest.mark.anyio
async def test_the_opening_quantity_is_what_was_left_at_the_end_of_the_previous_month(session):
    ing = await _ingredient(session, "NL còn lại cuối tháng")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)
    await _close(client, h, 202608)
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 6}]},
        headers=h,
    )
    assert issued.status_code == 201, issued.text
    await _move_consumption_to(session, ing, date(2026, 8, 20))
    await _receive(client, h, ing, 4, 2000, SEP)

    september = (await _close(client, h, 202609))[ing.id]

    # 4 left in August: (4 x 1.000 + 4 x 2.000) / 8; the 6 consumed no longer weigh.
    assert september["GiaBinhQuan"] == 1500


@pytest.mark.anyio
async def test_a_month_without_receipts_carries_the_nearest_earlier_average(session):
    ing = await _ingredient(session, "NL không nhập tháng 9")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)
    await _close(client, h, 202608)

    september = (await _close(client, h, 202609))[ing.id]

    assert september["GiaBinhQuan"] == 1000
    assert september["TongSoLuongNhap"] == 0
    # The carry skips months nobody closed: October still finds August's figure.
    october = (await _close(client, h, 202610))[ing.id]
    assert october["GiaBinhQuan"] == 1000


@pytest.mark.anyio
async def test_nothing_is_carried_for_an_ingredient_that_never_had_an_average(session):
    ing = await _ingredient(session, "NL chưa từng nhập")
    client = await _make_client(session)
    h, _ = await _headers(session)

    assert ing.id not in await _close(client, h, 202609)


@pytest.mark.anyio
async def test_an_exhausted_opening_stock_leaves_the_new_receipts_to_set_the_price(session):
    ing = await _ingredient(session, "NL hết tồn đầu kỳ")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)
    await _close(client, h, 202608)
    issued = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 10}]},
        headers=h,
    )
    assert issued.status_code == 201, issued.text
    await _move_consumption_to(session, ing, date(2026, 8, 31))
    await _receive(client, h, ing, 10, 2000, SEP)

    assert (await _close(client, h, 202609))[ing.id]["GiaBinhQuan"] == 2000


@pytest.mark.anyio
async def test_opening_stock_without_a_previous_average_cannot_be_priced_and_is_ignored(session):
    ing = await _ingredient(session, "NL tồn đầu chưa có giá")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)  # August was never closed
    await _receive(client, h, ing, 10, 2000, SEP)

    assert (await _close(client, h, 202609))[ing.id]["GiaBinhQuan"] == 2000


@pytest.mark.anyio
async def test_a_cancelled_receipt_neither_prices_nor_weighs_the_opening_stock(session):
    ing = await _ingredient(session, "NL phiếu hủy đầu kỳ")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)
    cancelled = await _receive(client, h, ing, 10, 5000, AUG)
    dropped = await client.delete(f"/api/v1/inventory/receipts/{cancelled}", headers=h)
    assert dropped.status_code == 200, dropped.text
    await _close(client, h, 202608)
    await _receive(client, h, ing, 10, 2000, SEP)

    assert (await _close(client, h, 202609))[ing.id]["GiaBinhQuan"] == 1500


@pytest.mark.anyio
async def test_closing_a_month_again_gives_the_same_figures(session):
    ing = await _ingredient(session, "NL chốt lại")
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, ing, 10, 1000, AUG)
    await _close(client, h, 202608)
    await _receive(client, h, ing, 10, 2000, SEP)

    first = (await _close(client, h, 202609))[ing.id]
    second = (await _close(client, h, 202609))[ing.id]

    assert first["GiaBinhQuan"] == second["GiaBinhQuan"] == 1500
