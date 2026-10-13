"""Inventory rules of the report: FR-INV-02, FR-INV-08/09/14, BR-LOT-01/02, NFR-20."""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select

from app.modules.catalog.models import Ingredient
from app.modules.inventory import costing
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    StockIssue,
    StockIssueLine,
    StockMovement,
)
from app.modules.sales.models import ItemHold
from app.modules.settings.models import SystemConfig
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from tests.helpers import FIXED_NOW

BASE = "/api/v1/inventory"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _ingredient(session, name="Bột", shelf_days=None, min_stock=None) -> Ingredient:
    ing = Ingredient(name=name, unit="kg", stock_qty=0, shelf_days=shelf_days, min_stock=min_stock)
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


async def _receive(client, token, ingredient, quantity, price=1000, when: datetime | None = None):
    body: dict = {
        "lines": [{"ingredient_id": ingredient.id, "quantity": quantity, "unit_price": price}]
    }
    if when is not None:
        body["receipt_date"] = when.isoformat()
    response = await client.post(f"{BASE}/receipts", json=body, headers=_auth(token))
    assert response.status_code == 201, response.text
    return response.json()["MaPhieuNhap"]


async def _lots(session, ingredient) -> list[IngredientLot]:
    return list(
        (
            await session.execute(
                select(IngredientLot)
                .where(IngredientLot.ingredient_id == ingredient.id)
                .order_by(IngredientLot.id)
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )


async def _movements(session, ingredient) -> list[StockMovement]:
    return list(
        (
            await session.execute(
                select(StockMovement)
                .where(StockMovement.ingredient_id == ingredient.id)
                .order_by(StockMovement.id)
                .execution_options(populate_existing=True)
            )
        )
        .scalars()
        .all()
    )


async def _stocktake(client, token, counts: list[tuple[int, int]]):
    created = await client.post(f"{BASE}/stocktakes", headers=_auth(token))
    assert created.status_code == 201, created.text
    sid = created.json()["MaPhieuKiemKe"]
    recorded = await client.post(
        f"{BASE}/stocktakes/{sid}/counts",
        json=[{"ingredient_id": i, "actual_qty": q} for i, q in counts],
        headers=_auth(token),
    )
    assert recorded.status_code == 200, recorded.text
    return sid


# --- FR-INV-02: receipts -----------------------------------------------------------------


async def test_a_receipt_is_refused_once_a_lot_was_partly_drawn(
    api_client, warehouse_token, session
):
    ing = await _ingredient(session)
    async with api_client as client:
        receipt_id = await _receive(client, warehouse_token, ing, 10)
        issued = await client.post(
            f"{BASE}/issues",
            json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 3}]},
            headers=_auth(warehouse_token),
        )
        assert issued.status_code == 201, issued.text
        cancel = await client.delete(
            f"{BASE}/receipts/{receipt_id}", headers=_auth(warehouse_token)
        )

    assert cancel.status_code == 422
    assert "kiểm kê" in cancel.json()["error"]["message"]
    await session.refresh(ing)
    assert ing.stock_qty == Decimal(7)
    assert (await session.get(GoodsReceipt, receipt_id)).status == "Nháp"


async def test_a_cancelled_receipt_reverses_its_lot_through_a_negative_receipt_movement(
    api_client, warehouse_token, session
):
    ing = await _ingredient(session)
    async with api_client as client:
        receipt_id = await _receive(client, warehouse_token, ing, 10)
        cancel = await client.delete(
            f"{BASE}/receipts/{receipt_id}", headers=_auth(warehouse_token)
        )

    assert cancel.status_code == 200
    movements = await _movements(session, ing)
    assert [(m.kind, m.qty, m.balance_after) for m in movements] == [
        ("Nhập", Decimal(10), Decimal(10)),
        ("Nhập", Decimal(-10), Decimal(0)),
    ]
    lot = (await _lots(session, ing))[0]
    assert {m.lot_id for m in movements} == {lot.id}
    assert lot.quantity_remaining == 0
    assert lot.status == "Đã dùng hết"
    entry = (
        await session.execute(
            select(SystemAuditLog).where(SystemAuditLog.action == "CANCEL_RECEIPT")
        )
    ).scalar_one()
    assert entry.before["TrangThai"] == "Nháp"
    assert entry.after["TrangThai"] == "Đã hủy"
    assert entry.user_id is not None


async def test_a_receipt_is_refused_while_its_lot_is_held(api_client, warehouse_token, session):
    ing = await _ingredient(session)
    async with api_client as client:
        receipt_id = await _receive(client, warehouse_token, ing, 10)
        lot = (await _lots(session, ing))[0]
        hold = ItemHold(
            selection_id="s",
            owner_id=3,
            dish_id=1,
            recipe_id=1,
            price_version_id=1,
            quantity=1,
            expires_at=FIXED_NOW + timedelta(minutes=5),
        )
        session.add(hold)
        await session.flush()
        from app.modules.sales.models import ItemHoldLot

        session.add(ItemHoldLot(hold_id=hold.id, lot_id=lot.id, quantity_held=Decimal(2)))
        await session.commit()
        cancel = await client.delete(
            f"{BASE}/receipts/{receipt_id}", headers=_auth(warehouse_token)
        )

    assert cancel.status_code == 422


async def test_creating_a_receipt_audits_its_lines_and_total(api_client, warehouse_token, session):
    ing = await _ingredient(session)
    async with api_client as client:
        receipt_id = await _receive(client, warehouse_token, ing, 4, price=2500)

    receipt = await session.get(GoodsReceipt, receipt_id)
    assert receipt.total == Decimal(10000)
    entry = (
        await session.execute(
            select(SystemAuditLog).where(SystemAuditLog.action == "CREATE_RECEIPT")
        )
    ).scalar_one()
    assert entry.after["TongTien"] == 10000
    assert entry.after["DongNhap"][0]["MaNguyenLieu"] == ing.id


# --- FR-INV-14, BR-LOT-01: lot status by expiry --------------------------------------------


async def test_lot_status_follows_the_expiry_date_and_the_configured_warning_days(
    api_client, warehouse_token, session, monkeypatch
):
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 10, 0))
    ing = await _ingredient(session, shelf_days=10)
    async with api_client as client:
        # Received 2026-09-14 -> expires today; 09-16 -> in 2 days; 09-24 -> in 10 days.
        for received in (datetime(2026, 9, 13), datetime(2026, 9, 14), datetime(2026, 9, 24)):
            await _receive(client, warehouse_token, ing, 1, when=received)
        statuses = lambda body: [row["TrangThaiHanSuDung"] for row in body["items"]]  # noqa: E731
        body = (await client.get(f"{BASE}/lots", headers=_auth(warehouse_token))).json()
        assert statuses(body) == ["Hết hạn", "Sắp hết hạn", "Còn hạn"]
        assert [row["SoNgayConLai"] for row in body["items"]] == [-1, 0, 10]

        config = await session.get(SystemConfig, 1)
        config.expiry_warning_days = 12
        await session.commit()
        body = (await client.get(f"{BASE}/lots", headers=_auth(warehouse_token))).json()
        assert statuses(body) == ["Hết hạn", "Sắp hết hạn", "Sắp hết hạn"]

    assert [lot.status for lot in await _lots(session, ing)] == [
        "Hết hạn",
        "Sắp hết hạn",
        "Sắp hết hạn",
    ]


async def test_an_expired_lot_is_never_drawn_for_a_normal_issue(
    api_client, warehouse_token, session, monkeypatch
):
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 10, 0))
    ing = await _ingredient(session, shelf_days=3)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 5, when=datetime(2026, 9, 1))  # expired
        await _receive(client, warehouse_token, ing, 4, when=datetime(2026, 9, 24))
        too_much = await client.post(
            f"{BASE}/issues",
            json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 6}]},
            headers=_auth(warehouse_token),
        )
        ok = await client.post(
            f"{BASE}/issues",
            json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 4}]},
            headers=_auth(warehouse_token),
        )
        expired_write_off = await client.post(
            f"{BASE}/issues",
            json={"reason": "Hết hạn", "lines": [{"ingredient_id": ing.id, "quantity": 5}]},
            headers=_auth(warehouse_token),
        )

    assert too_much.status_code == 422
    assert ok.status_code == 201
    assert expired_write_off.status_code == 201
    expired_lot, fresh_lot = await _lots(session, ing)
    assert fresh_lot.quantity_remaining == 0
    assert expired_lot.quantity_remaining == 0


async def test_dish_availability_ignores_expired_stock(session, monkeypatch):
    from app.modules.catalog.models import Dish, DishGroup, Recipe, RecipeItem
    from app.modules.inventory.stock import dish_is_out_of_stock

    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 10, 0))
    ing = await _ingredient(session)
    group = DishGroup(name="Món chính", display_order=1)
    session.add(group)
    await session.flush()
    dish = Dish(name="Phở", group_id=group.id, missing_recipe=False)
    session.add(dish)
    await session.flush()
    recipe = Recipe(
        dish_id=dish.id,
        business_date=date(2026, 9, 1),
        status="Đang áp dụng",
        change_type="Tạo mới",
    )
    session.add(recipe)
    await session.flush()
    session.add(RecipeItem(recipe_id=recipe.id, ingredient_id=ing.id, quantity=Decimal(1)))
    session.add(
        IngredientLot(
            ingredient_id=ing.id, quantity_remaining=Decimal(5), expiry_date=date(2026, 9, 23)
        )
    )
    await session.flush()
    assert await dish_is_out_of_stock(session, dish.id) is True

    session.add(
        IngredientLot(
            ingredient_id=ing.id, quantity_remaining=Decimal(5), expiry_date=date(2026, 9, 24)
        )
    )
    await session.flush()
    assert await dish_is_out_of_stock(session, dish.id) is False


# --- FR-INV-08/09, BR-LOT-02, NFR-20: stocktake -------------------------------------------


async def test_a_stocktake_surplus_tops_up_the_latest_valid_lot_without_a_fake_receipt(
    api_client, warehouse_token, session, monkeypatch
):
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 10, 0))
    ing = await _ingredient(session, shelf_days=30)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 5, when=datetime(2026, 9, 10))
        await _receive(client, warehouse_token, ing, 5, when=datetime(2026, 9, 20))
        receipts_before = len((await session.execute(select(GoodsReceipt))).scalars().all())
        sid = await _stocktake(client, warehouse_token, [(ing.id, 13)])
        confirm = await client.post(
            f"{BASE}/stocktakes/{sid}/confirm", headers=_auth(warehouse_token)
        )

    assert confirm.status_code == 200, confirm.text
    older, newer = await _lots(session, ing)
    assert (older.quantity_remaining, newer.quantity_remaining) == (Decimal(5), Decimal(8))
    assert len((await session.execute(select(GoodsReceipt))).scalars().all()) == receipts_before
    adjustment = (await _movements(session, ing))[-1]
    assert (adjustment.kind, adjustment.qty, adjustment.lot_id) == (
        "Điều chỉnh kiểm kê",
        Decimal(3),
        newer.id,
    )
    assert adjustment.stocktake_line_id is not None
    assert adjustment.balance_after == Decimal(13)
    await session.refresh(ing)
    assert ing.stock_qty == Decimal(13)


async def test_a_surplus_with_no_valid_lot_creates_an_adjustment_lot(
    api_client, warehouse_token, session, monkeypatch
):
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 10, 0))
    ing = await _ingredient(session, shelf_days=3)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 5, when=datetime(2026, 9, 1))  # expired
        sid = await _stocktake(client, warehouse_token, [(ing.id, 7)])
        confirm = await client.post(
            f"{BASE}/stocktakes/{sid}/confirm", headers=_auth(warehouse_token)
        )

    assert confirm.status_code == 200, confirm.text
    expired, adjustment = await _lots(session, ing)
    assert expired.quantity_remaining == 5
    assert adjustment.is_adjustment is True
    assert adjustment.receipt_line_id is None
    assert adjustment.expiry_date is None
    assert adjustment.quantity_remaining == 2
    assert adjustment.received_quantity == 2
    assert adjustment.received_at.date() == date(2026, 9, 24)
    assert (await _movements(session, ing))[-1].lot_id == adjustment.id


async def test_a_stocktake_shortage_consumes_expired_lots_and_writes_the_voucher(
    api_client, warehouse_token, session, monkeypatch
):
    monkeypatch.setattr(business_date, "now", lambda: datetime(2026, 9, 24, 10, 0))
    ing = await _ingredient(session, shelf_days=3)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 4, when=datetime(2026, 9, 1))  # expired
        await _receive(client, warehouse_token, ing, 6, when=datetime(2026, 9, 24))
        sid = await _stocktake(client, warehouse_token, [(ing.id, 3)])
        confirm = await client.post(
            f"{BASE}/stocktakes/{sid}/confirm", headers=_auth(warehouse_token)
        )

    assert confirm.status_code == 200, confirm.text
    expired, fresh = await _lots(session, ing)
    assert (expired.quantity_remaining, fresh.quantity_remaining) == (Decimal(0), Decimal(3))
    kinds = [(m.kind, m.qty) for m in (await _movements(session, ing))[2:]]
    assert kinds == [("Điều chỉnh kiểm kê", Decimal(-4)), ("Điều chỉnh kiểm kê", Decimal(-3))]
    voucher = (await session.execute(select(StockIssue))).scalar_one()
    assert (voucher.source, voucher.stocktake_id) == ("Kiểm kê", sid)
    voucher_line = (await session.execute(select(StockIssueLine))).scalar_one()
    assert (voucher_line.ingredient_id, voucher_line.quantity) == (ing.id, Decimal(7))
    # The voucher classifies the loss; only the adjustments moved the stock.
    assert not [m for m in await _movements(session, ing) if m.kind == "Xuất thủ công"]
    await session.refresh(ing)
    assert ing.stock_qty == Decimal(3)


async def test_a_stocktake_cannot_open_over_live_holds(api_client, warehouse_token, session):
    ing = await _ingredient(session)
    session.add(
        ItemHold(
            selection_id="s",
            owner_id=3,
            dish_id=1,
            recipe_id=1,
            price_version_id=1,
            quantity=1,
            expires_at=FIXED_NOW + timedelta(minutes=5),
        )
    )
    await session.commit()
    async with api_client as client:
        refused = await client.post(f"{BASE}/stocktakes", headers=_auth(warehouse_token))

    assert refused.status_code == 422
    assert "giữ chỗ" in refused.json()["error"]["message"]
    assert ing.id  # the ingredient exists; the hold alone is the reason


async def test_a_stocktake_session_blocks_every_stock_writer(api_client, warehouse_token, session):
    ing = await _ingredient(session)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 5)
        await _stocktake(client, warehouse_token, [(ing.id, 5)])
        receipt = await client.post(
            f"{BASE}/receipts",
            json={"lines": [{"ingredient_id": ing.id, "quantity": 1, "unit_price": 1}]},
            headers=_auth(warehouse_token),
        )
        issue = await client.post(
            f"{BASE}/issues",
            json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
            headers=_auth(warehouse_token),
        )

    assert receipt.status_code == 422
    assert issue.status_code == 422
    assert "kiểm kê" in receipt.json()["error"]["message"]


async def test_confirming_refuses_stock_that_moved_after_the_count(
    api_client, warehouse_token, session
):
    ing = await _ingredient(session)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 5)
        sid = await _stocktake(client, warehouse_token, [(ing.id, 4)])
        ing.stock_qty = Decimal(9)  # something bypassed the session lock
        await session.commit()
        confirm = await client.post(
            f"{BASE}/stocktakes/{sid}/confirm", headers=_auth(warehouse_token)
        )

    assert confirm.status_code == 422
    assert "thay đổi" in confirm.json()["error"]["message"]


async def test_stocktake_roles_are_kitchen_and_manager_only(api_client, cashier_token, session):
    async with api_client as client:
        response = await client.post(f"{BASE}/stocktakes", headers=_auth(cashier_token))
        stock = await client.get(f"{BASE}/stock", headers=_auth(cashier_token))
        costing_close = await client.post(
            f"{BASE}/costing/202609/close", headers=_auth(cashier_token)
        )

    assert response.status_code == 403
    assert stock.status_code == 403
    assert costing_close.status_code == 403


# --- costing -----------------------------------------------------------------------------


async def test_closing_a_month_ignores_cancelled_receipts_and_stocktake_adjustment_lots(
    api_client, warehouse_token, session
):
    ing = await _ingredient(session)
    when = datetime(2026, 9, 10)
    async with api_client as client:
        await _receive(client, warehouse_token, ing, 10, price=100, when=when)
        cancelled_id = await _receive(client, warehouse_token, ing, 10, price=900, when=when)
        cancel = await client.delete(
            f"{BASE}/receipts/{cancelled_id}", headers=_auth(warehouse_token)
        )
        assert cancel.status_code == 200
    # What older stocktakes left behind: a zero-price receipt backing an adjustment lot.
    fake = GoodsReceipt(status="Nháp", receipt_date=when)
    session.add(fake)
    await session.flush()
    line = GoodsReceiptLine(
        receipt_id=fake.id, ingredient_id=ing.id, quantity=Decimal(10), unit_price=Decimal(0)
    )
    session.add(line)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ing.id,
            receipt_line_id=line.id,
            quantity_remaining=Decimal(10),
            is_adjustment=True,
        )
    )
    await session.commit()

    rows = await costing.close_month(session, 202609)

    assert [(r.ingredient_id, r.avg_cost, r.total_qty) for r in rows] == [
        (ing.id, Decimal(100), Decimal(10))
    ]
