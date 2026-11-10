"""Stocktakes and write-offs are previewed before anything is written (FR-INV-05/08)."""

import pytest
from sqlalchemy import func, select

from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import (
    IngredientLot,
    StockIssue,
    StockIssueLine,
    StockMovement,
    Stocktake,
)
from tests.modules.test_inventory_costing import (
    _headers,
    _ingredient,
    _make_client,
    _receive,
)

pytestmark = pytest.mark.anyio


async def _open(client, headers):
    created = await client.post("/api/v1/inventory/stocktakes", headers=headers)
    assert created.status_code == 201, created.text
    return created.json()["MaPhieuKiemKe"]


async def _preview(client, headers, sid, ingredient_id, actual, reason=None):
    return await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/preview",
        json=[{"ingredient_id": ingredient_id, "actual_qty": actual, "reason": reason}],
        headers=headers,
    )


async def _state(session, ingredient_id):
    """Everything a preview must leave alone."""
    session.expire_all()
    return {
        "stock": await session.scalar(
            select(Ingredient.stock_qty).where(Ingredient.id == ingredient_id)
        ),
        "lots": list(
            await session.scalars(
                select(IngredientLot.quantity_remaining)
                .where(IngredientLot.ingredient_id == ingredient_id)
                .order_by(IngredientLot.id)
            )
        ),
        "movements": await session.scalar(select(func.count()).select_from(StockMovement)),
        "issues": await session.scalar(select(func.count()).select_from(StockIssue)),
        "issue_lines": await session.scalar(select(func.count()).select_from(StockIssueLine)),
    }


async def test_a_stocktake_preview_shows_before_after_and_difference_without_writing(session):
    """TC-INV-52: 500 on the books, 470 counted."""
    iid = (await _ingredient(session, "Bò")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 500, 200)
    sid = await _open(client, h)
    before = await _state(session, iid)

    preview = await _preview(client, h, sid, iid, 470, "hao hụt")

    assert preview.status_code == 200, preview.text
    (row,) = preview.json()["items"]
    assert (row["TonTruocDieuChinh"], row["TonSauDieuChinh"], row["ChenhLech"]) == (500, 470, -30)
    assert row["TenNguyenLieu"] == "Bò"
    assert await _state(session, iid) == before
    assert await session.scalar(select(Stocktake.status).where(Stocktake.id == sid)) == (
        "Đang kiểm kê"
    )
    # The session is still open, so the storeroom is still locked.
    blocked = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": iid, "quantity": 1}]},
        headers=h,
    )
    assert blocked.status_code == 422


async def test_going_back_and_matching_the_books_confirms_without_an_adjustment(session):
    """TC-INV-53: preview 80, go back, count 100, confirm: no adjustment movement."""
    iid = (await _ingredient(session, "Hành")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 100, 40)
    sid = await _open(client, h)
    before = await _state(session, iid)

    first = await _preview(client, h, sid, iid, 80, "đếm thiếu")
    assert first.json()["items"][0]["ChenhLech"] == -20
    assert await _state(session, iid) == before
    second = await _preview(client, h, sid, iid, 100)
    assert second.json()["items"][0]["ChenhLech"] == 0
    counts = [{"ingredient_id": iid, "actual_qty": 100}]
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/counts", json=counts, headers=h)
    confirmed = await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)

    assert confirmed.status_code == 200, confirmed.text
    assert await _state(session, iid) == before
    assert await session.scalar(select(Stocktake.status).where(Stocktake.id == sid)) == (
        "Đã xác nhận"
    )


async def test_cancelling_after_a_preview_leaves_stock_alone_and_unlocks(session):
    """TC-INV-54: a previewed shortage that was never confirmed writes nothing."""
    iid = (await _ingredient(session, "Bò hủy phiên")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 500, 200)
    sid = await _open(client, h)
    before = await _state(session, iid)
    await _preview(client, h, sid, iid, 470, "hao hụt")

    cancelled = await client.post(f"/api/v1/inventory/stocktakes/{sid}/cancel", headers=h)

    assert cancelled.status_code == 200, cancelled.text
    assert await _state(session, iid) == before
    assert await session.scalar(select(Stocktake.status).where(Stocktake.id == sid)) == "Đã hủy"
    unlocked = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": iid, "quantity": 1}]},
        headers=h,
    )
    assert unlocked.status_code == 201, unlocked.text


async def test_a_stocktake_preview_is_refused_once_the_session_is_closed(session):
    iid = (await _ingredient(session, "NL phiên đã đóng")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    sid = await _open(client, h)
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/cancel", headers=h)

    assert (await _preview(client, h, sid, iid, 1)).status_code == 422
    assert (await _preview(client, h, 999_999, iid, 1)).status_code == 404


async def test_a_stocktake_preview_rejects_what_the_count_itself_would_reject(session):
    iid = (await _ingredient(session, "NL trùng")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    sid = await _open(client, h)

    negative = await _preview(client, h, sid, iid, -1)
    duplicated = await client.post(
        f"/api/v1/inventory/stocktakes/{sid}/preview",
        json=[{"ingredient_id": iid, "actual_qty": 1}, {"ingredient_id": iid, "actual_qty": 2}],
        headers=h,
    )

    assert negative.status_code == 422
    assert duplicated.status_code == 422


async def test_a_cashier_cannot_preview_a_stocktake(session):
    client = await _make_client(session)
    cashier, _ = await _headers(session, role="CASHIER", username="cashier_preview")

    assert (await _preview(client, cashier, 1, 1, 1)).status_code == 403


async def _preview_issue(client, headers, lines, reason="Hư hỏng"):
    return await client.post(
        "/api/v1/inventory/issues/preview",
        json={"reason": reason, "lines": lines},
        headers=headers,
    )


async def test_a_write_off_is_written_once_and_only_after_the_preview_is_confirmed(session):
    """TC-INV-55: preview 100, go back, 80, confirm: one voucher, one movement, lot 420."""
    iid = (await _ingredient(session, "Bò xuất hủy")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 500, 200)
    before = await _state(session, iid)

    first = await _preview_issue(client, h, [{"ingredient_id": iid, "quantity": 100}])

    assert first.status_code == 200, first.text
    (line,) = first.json()["lines"]
    assert (line["SoLuongHuy"], line["TonLoConLai"], line["GiaTri"]) == (100, 400, 20_000)
    assert first.json()["TongGiaTri"] == 20_000
    assert first.json()["LuotGiuBiGiaiPhong"] == []
    assert await _state(session, iid) == before

    second = await _preview_issue(client, h, [{"ingredient_id": iid, "quantity": 80}])
    assert second.json()["lines"][0]["TonLoConLai"] == 420
    assert await _state(session, iid) == before
    created = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hư hỏng", "lines": [{"ingredient_id": iid, "quantity": 80}]},
        headers=h,
    )

    assert created.status_code == 201, created.text
    after = await _state(session, iid)
    assert after["issues"] == before["issues"] + 1
    assert after["movements"] == before["movements"] + 1
    assert after["lots"] == [420]
    session.expire_all()
    written = (await session.execute(select(StockIssueLine))).scalar_one()
    assert (written.quantity, written.estimated_cost) == (80, 16_000)


async def test_a_write_off_preview_follows_fifo_across_lots(session):
    iid = (await _ingredient(session, "NL hai lô")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 3, 100)
    await _receive(client, h, iid, 5, 100)

    preview = await _preview_issue(client, h, [{"ingredient_id": iid, "quantity": 4}])

    lines = preview.json()["lines"]
    assert [(line["SoLuongHuy"], line["TonLoConLai"]) for line in lines] == [(3, 0), (1, 4)]
    assert preview.json()["TongGiaTri"] == 400


async def test_a_write_off_preview_of_an_unpriced_ingredient_reports_an_unknown_value(session):
    """FR-INV-05: "Chưa xác định" is None in the API, never 0."""
    iid = (await _ingredient(session, "Sả")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    sid = await _open(client, h)
    counts = [{"ingredient_id": iid, "actual_qty": 200, "reason": "thừa"}]
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/counts", json=counts, headers=h)
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)

    preview = await _preview_issue(client, h, [{"ingredient_id": iid, "quantity": 50}])

    assert preview.status_code == 200, preview.text
    assert preview.json()["lines"][0]["GiaTri"] is None
    assert preview.json()["TongGiaTri"] is None


async def test_a_write_off_preview_refuses_what_the_write_off_would_refuse(session):
    iid = (await _ingredient(session, "NL không đủ")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receive(client, h, iid, 2, 100)

    too_much = await _preview_issue(client, h, [{"ingredient_id": iid, "quantity": 3}])
    wrong_source = await client.post(
        "/api/v1/inventory/issues/preview",
        json={"source": "Món đã chế biến", "lines": [{"order_line_id": 1, "servings": 1}]},
        headers=h,
    )
    sid = await _open(client, h)
    while_counting = await _preview_issue(client, h, [{"ingredient_id": iid, "quantity": 1}])

    assert too_much.status_code == 422
    assert wrong_source.status_code == 422
    assert sid and while_counting.status_code == 422


async def _stock_row(client, headers, name):
    listed = await client.get("/api/v1/inventory/stock", params={"search": name}, headers=headers)
    assert listed.status_code == 200, listed.text
    (row,) = listed.json()["items"]
    return row


async def test_the_stock_list_shows_the_unit_cost_and_the_value_of_the_stock(session):
    """TC-INV-56: 10 kg at 200.000 then 10 kg at 260.000: 230.000 and 4.600.000."""
    iid = (await _ingredient(session, "Bò tồn kho")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    first = await _receive(client, h, iid, 10, 200_000)
    second = await _receive(client, h, iid, 10, 260_000)

    row = await _stock_row(client, h, "Bò tồn kho")
    history = await client.get(f"/api/v1/inventory/stock/{iid}/cost-history", headers=h)

    assert (row["DonGiaBinhQuan"], row["GiaTriTon"]) == (230_000, 4_600_000)
    assert history.status_code == 200, history.text
    assert history.json()["total"] == 2
    newest, oldest = history.json()["items"]
    assert (newest["DonGiaBinhQuan"], newest["SoLuongTon"]) == (230_000, 20)
    assert (oldest["DonGiaBinhQuan"], oldest["SoLuongTon"]) == (200_000, 10)
    assert newest["ChungTu"] == f"Phiếu nhập #{second}"
    assert oldest["ChungTu"] == f"Phiếu nhập #{first}"
    assert newest["ThoiDiemHieuLuc"] > oldest["ThoiDiemHieuLuc"]


async def test_the_cost_history_names_the_document_behind_each_recalculation(session):
    iid = (await _ingredient(session, "NL chứng từ")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    kept = await _receive(client, h, iid, 10, 100)
    cancelled = await _receive(client, h, iid, 10, 300)
    line = (
        (
            await session.execute(
                select(StockMovement.receipt_line_id).where(StockMovement.ingredient_id == iid)
            )
        )
        .scalars()
        .first()
    )
    await client.patch(
        f"/api/v1/inventory/receipts/{kept}",
        json={"lines": [{"line_id": line, "quantity": 10, "unit_price": 120}]},
        headers=h,
    )
    await client.delete(f"/api/v1/inventory/receipts/{cancelled}", headers=h)

    history = await client.get(f"/api/v1/inventory/stock/{iid}/cost-history", headers=h)

    assert [item["ChungTu"] for item in history.json()["items"]] == [
        f"Hủy phiếu nhập #{cancelled}",
        "Sửa đơn giá phiếu nhập",
        f"Phiếu nhập #{cancelled}",
        f"Phiếu nhập #{kept}",
    ]


async def test_an_unpriced_ingredient_lists_unknown_cost_and_value_not_zero(session):
    """TC-INV-57: surplus of 200 with no receipt: both figures are null in the API."""
    iid = (await _ingredient(session, "Sả tồn kho")).id
    client = await _make_client(session)
    h, _ = await _headers(session)
    sid = await _open(client, h)
    counts = [{"ingredient_id": iid, "actual_qty": 200, "reason": "thừa"}]
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/counts", json=counts, headers=h)
    await client.post(f"/api/v1/inventory/stocktakes/{sid}/confirm", headers=h)

    row = await _stock_row(client, h, "Sả tồn kho")
    history = await client.get(f"/api/v1/inventory/stock/{iid}/cost-history", headers=h)

    assert row["SoLuongTon"] == 200
    assert row["DonGiaBinhQuan"] is None
    assert row["GiaTriTon"] is None
    assert history.json() == {"items": [], "total": 0, "page": 1, "page_size": 20}


async def test_a_cashier_cannot_read_the_cost_history(session):
    client = await _make_client(session)
    cashier, _ = await _headers(session, role="CASHIER", username="cashier_cost")

    denied = await client.get("/api/v1/inventory/stock/1/cost-history", headers=cashier)

    assert denied.status_code == 403
