"""FR-INV-05/06, BR-LOT-02 and FR-REP-05: write-off of prepared dishes.

The "Món đã chế biến" voucher only classifies a consumption that the sale already booked: it
moves no stock, creates no ledger row, and its cost stays inside 05a/05c (never added to 05b).
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select

from app.modules.catalog.models import Ingredient
from app.modules.inventory import costing
from app.modules.inventory.models import (
    IngredientLot,
    MonthlyAverageCost,
    StockIssue,
    StockIssueLine,
    StockMovement,
)
from app.modules.reports import queries
from app.modules.reports.periods import month_period
from app.modules.sales.models import OrderLine
from app.shared.audit import SystemAuditLog
from tests.modules.conftest import _r_dish, _r_line, _r_order, _r_recipe

BASE = "/api/v1/inventory"
WRITE_OFF = f"{BASE}/issues/dishes"
SOURCE = "Món đã chế biến"
SEP_10 = date(2026, 9, 10)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@dataclass
class Prepared:
    line: OrderLine
    ingredients: list[Ingredient]
    per_portion: Decimal


async def _prepared(
    session,
    *,
    servings: int = 3,
    per_portion: str = "2",
    status: str = "Đã xác nhận xong",
    ingredients: int = 1,
    average: str | None = None,
    bd: date = SEP_10,
    order_status: str = "Đang mở",
    consumed: bool = True,
    recipe: bool = True,
) -> Prepared:
    """A dish line whose sale already drew `servings x per_portion` of each ingredient."""
    dish = await _r_dish(session, f"Món xuất hủy {servings}-{status}-{ingredients}")
    made: list[Ingredient] = []
    for index in range(ingredients):
        ingredient = Ingredient(
            name=f"NL xuất hủy {dish.id}-{index}",
            unit="kg",
            min_stock=0,
            stock_qty=Decimal(14),
            is_deleted=False,
        )
        session.add(ingredient)
        await session.flush()
        session.add(
            IngredientLot(
                ingredient_id=ingredient.id,
                quantity_remaining=Decimal(14),
                received_quantity=Decimal(20),
                status="Còn hạn",
                received_at=datetime(2026, 9, 1, 8, 0),
            )
        )
        if average is not None:
            session.add(
                MonthlyAverageCost(
                    ingredient_id=ingredient.id,
                    month=bd.year * 100 + bd.month,
                    avg_cost=Decimal(average),
                    total_qty=Decimal(1),
                )
            )
        made.append(ingredient)
    the_recipe = None
    if recipe:
        the_recipe = await _r_recipe(session, dish, made[0], per_portion, bd)
        for extra in made[1:]:
            from app.modules.catalog.models import RecipeItem

            session.add(
                RecipeItem(
                    recipe_id=the_recipe.id,
                    ingredient_id=extra.id,
                    quantity=Decimal(per_portion),
                )
            )
    order = await _r_order(session, bd=bd, status=order_status, order_type="Mang về")
    line = await _r_line(
        session,
        order,
        dish,
        servings,
        50000,
        status=status,
        recipe_id=the_recipe.id if the_recipe else None,
    )
    if consumed:
        for ingredient in made:
            session.add(
                StockMovement(
                    ingredient_id=ingredient.id,
                    kind="Trừ tự động",
                    qty=-Decimal(per_portion) * servings,
                    balance_after=Decimal(14),
                    business_date=bd,
                    order_line_id=line.id,
                )
            )
    await session.commit()
    return Prepared(line=line, ingredients=made, per_portion=Decimal(per_portion))


def _body(*pairs: tuple[int, int], reason: str = "Hư hỏng") -> dict:
    return {
        "reason": reason,
        "lines": [{"order_line_id": line_id, "servings": servings} for line_id, servings in pairs],
    }


async def _vouchers(session) -> list[StockIssue]:
    return list(
        (await session.execute(select(StockIssue).where(StockIssue.source == SOURCE)))
        .scalars()
        .all()
    )


async def _movement_count(session) -> int:
    return (await session.execute(select(func.count(StockMovement.id)))).scalar_one()


# --- happy path: classification only ------------------------------------------------------


async def test_writing_off_prepared_dishes_records_the_original_consumption_without_moving_stock(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3, per_portion="2", ingredients=2)
    ledger_before = await _movement_count(session)

    response = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 2)), headers=_auth(warehouse_token)
    )

    assert response.status_code == 201, response.text
    voucher = (await _vouchers(session))[0]
    assert response.json()["MaPhieuXuat"] == voucher.id
    assert (voucher.source, voucher.reason, voucher.stocktake_id) == (SOURCE, "Hư hỏng", None)
    assert voucher.created_by == 3
    lines = (
        (
            await session.execute(
                select(StockIssueLine)
                .where(StockIssueLine.issue_id == voucher.id)
                .order_by(StockIssueLine.ingredient_id)
            )
        )
        .scalars()
        .all()
    )
    assert [(ln.ingredient_id, ln.quantity, ln.order_line_id, ln.servings) for ln in lines] == [
        (ingredient.id, Decimal(4), prepared.line.id, 2) for ingredient in prepared.ingredients
    ]
    # No stock moved: the sale's own movements remain the only ledger rows (FR-INV-05).
    assert await _movement_count(session) == ledger_before
    for ingredient in prepared.ingredients:
        await session.refresh(ingredient)
        assert ingredient.stock_qty == Decimal(14)
    lots = (await session.execute(select(IngredientLot.quantity_remaining))).scalars().all()
    assert set(lots) == {Decimal(14)}


async def test_a_manager_may_write_off_prepared_dishes_too(api_client, manager_token, session):
    prepared = await _prepared(session)

    response = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(manager_token)
    )

    assert response.status_code == 201, response.text


async def test_a_served_dish_can_be_written_off(api_client, warehouse_token, session):
    prepared = await _prepared(session, status="Đã phục vụ")

    response = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    assert response.status_code == 201, response.text


async def test_the_audit_log_keeps_the_servings_before_and_after(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3)
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 2)), headers=_auth(warehouse_token)
    )

    entries = (
        (
            await session.execute(
                select(SystemAuditLog)
                .where(SystemAuditLog.action == "DISH_STOCK_WRITE_OFF")
                .order_by(SystemAuditLog.id)
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 2
    second = entries[1]
    assert second.user_id == 3
    assert second.target_entity == "PHIEU_XUAT_KHO"
    assert second.before["DongMon"] == [
        {"MaChiTietOrder": prepared.line.id, "SoSuatDaHuy": 1, "SoSuatTieuHao": 3}
    ]
    assert second.after["DongMon"] == [
        {"MaChiTietOrder": prepared.line.id, "SoSuatHuy": 2, "SoSuatDaHuy": 3}
    ]
    assert second.after["NguonXuat"] == SOURCE


# --- FR-INV-06: never more than the consumed servings not yet written off ------------------


async def test_servings_accumulate_per_line_across_vouchers_and_stop_at_the_consumed_total(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3)
    for servings in (2, 1):
        ok = await api_client.post(
            WRITE_OFF, json=_body((prepared.line.id, servings)), headers=_auth(warehouse_token)
        )
        assert ok.status_code == 201, ok.text

    over = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    assert over.status_code == 422
    assert len(await _vouchers(session)) == 2


async def test_servings_above_the_consumed_quantity_are_refused_at_the_boundary(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3)

    over = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 4)), headers=_auth(warehouse_token)
    )
    exact = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 3)), headers=_auth(warehouse_token)
    )

    assert over.status_code == 422
    assert exact.status_code == 201, exact.text


async def test_the_same_line_twice_in_one_request_is_summed_before_the_check(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3, ingredients=2)

    too_many = await api_client.post(
        WRITE_OFF,
        json=_body((prepared.line.id, 2), (prepared.line.id, 2)),
        headers=_auth(warehouse_token),
    )
    fits = await api_client.post(
        WRITE_OFF,
        json=_body((prepared.line.id, 1), (prepared.line.id, 2)),
        headers=_auth(warehouse_token),
    )

    assert too_many.status_code == 422
    assert fits.status_code == 201, fits.text
    voucher_lines = (await session.execute(select(StockIssueLine))).scalars().all()
    # One row per ingredient, carrying the summed servings once - not once per ingredient row.
    assert sorted((ln.ingredient_id, ln.servings, ln.quantity) for ln in voucher_lines) == sorted(
        (ingredient.id, 3, Decimal(6)) for ingredient in prepared.ingredients
    )


async def test_one_bad_line_rejects_the_whole_write_off(api_client, warehouse_token, session):
    good = await _prepared(session, servings=3)
    bad = await _prepared(session, servings=1)
    audit_before = (await session.execute(select(func.count(SystemAuditLog.id)))).scalar_one()

    response = await api_client.post(
        WRITE_OFF,
        json=_body((good.line.id, 1), (bad.line.id, 2)),
        headers=_auth(warehouse_token),
    )

    assert response.status_code == 422
    assert await _vouchers(session) == []
    assert (await session.execute(select(func.count(StockIssueLine.id)))).scalar_one() == 0
    assert (
        await session.execute(select(func.count(SystemAuditLog.id)))
    ).scalar_one() == audit_before


# --- validation -----------------------------------------------------------------------------


async def test_the_request_is_validated(api_client, warehouse_token, session):
    prepared = await _prepared(session)
    headers = _auth(warehouse_token)
    line = prepared.line.id

    for body in (
        _body((line, 0)),
        _body((line, -1)),
        {"reason": "Hư hỏng", "lines": []},
        _body((line, 1), reason=""),
        _body((line, 1), reason="x" * 51),
        {"lines": [{"order_line_id": line, "servings": 1}]},
        {"reason": "Hư hỏng", "lines": [{"order_line_id": line, "servings": 1.5}]},
    ):
        response = await api_client.post(WRITE_OFF, json=body, headers=headers)
        assert response.status_code == 422, body
    assert await _vouchers(session) == []


async def test_an_unknown_order_line_is_not_found(api_client, warehouse_token, session):
    response = await api_client.post(
        WRITE_OFF, json=_body((987654, 1)), headers=_auth(warehouse_token)
    )

    assert response.status_code == 404
    assert "dòng món" in response.json()["error"]["message"]
    assert await _vouchers(session) == []


async def test_only_dishes_that_were_actually_prepared_can_be_written_off(
    api_client, warehouse_token, session
):
    waiting = await _prepared(session, status="Chờ làm")
    cancelled = await _prepared(session, status="Đã hủy")

    for prepared in (waiting, cancelled):
        response = await api_client.post(
            WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
        )
        assert response.status_code == 422
    assert await _vouchers(session) == []


async def test_a_dish_without_a_recipe_or_a_booked_consumption_is_refused(
    api_client, warehouse_token, session
):
    no_recipe = await _prepared(session, recipe=False, consumed=False)
    never_drawn = await _prepared(session, consumed=False)
    returned = await _prepared(session)
    session.add(
        StockMovement(
            ingredient_id=returned.ingredients[0].id,
            kind="Hoàn kho",
            qty=Decimal(6),
            balance_after=Decimal(14),
            business_date=SEP_10,
            order_line_id=returned.line.id,
        )
    )
    await session.commit()

    for prepared in (no_recipe, never_drawn, returned):
        response = await api_client.post(
            WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
        )
        assert response.status_code == 422
    assert await _vouchers(session) == []


# --- permissions and the stocktake lock -------------------------------------------------------


async def test_cashiers_and_anonymous_callers_cannot_write_off(api_client, cashier_token, session):
    prepared = await _prepared(session)

    forbidden = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(cashier_token)
    )
    anonymous = await api_client.post(WRITE_OFF, json=_body((prepared.line.id, 1)))

    assert forbidden.status_code == 403
    assert anonymous.status_code == 401
    assert await _vouchers(session) == []


async def test_an_open_stocktake_blocks_the_write_off(api_client, warehouse_token, session):
    prepared = await _prepared(session)
    opened = await api_client.post(f"{BASE}/stocktakes", headers=_auth(warehouse_token))
    assert opened.status_code == 201, opened.text

    response = await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    assert response.status_code == 422
    assert await _vouchers(session) == []


# --- cost: classified, never added a second time (FR-REP-05) --------------------------------


async def test_the_voucher_is_costed_with_the_average_of_the_orders_month(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3, per_portion="2", average="1500")

    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 2)), headers=_auth(warehouse_token)
    )

    line = (await session.execute(select(StockIssueLine))).scalar_one()
    assert line.estimated_cost == Decimal(6000)  # 2 servings x 2 x 1.500


async def test_a_voucher_without_a_monthly_average_stays_provisional_until_the_month_is_closed(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session)
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )
    line = (await session.execute(select(StockIssueLine))).scalar_one()
    assert line.estimated_cost == 0

    session.add(
        MonthlyAverageCost(
            ingredient_id=prepared.ingredients[0].id,
            month=202609,
            avg_cost=Decimal(1000),
            total_qty=Decimal(1),
        )
    )
    await session.flush()
    priced = await costing.backfill_issue_costs(session, 202609)

    assert priced == 1
    await session.refresh(line)
    assert line.estimated_cost == Decimal(2000)


async def test_the_backfill_prices_by_the_month_of_the_order_not_of_the_voucher(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, bd=date(2026, 8, 31))
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )
    session.add_all(
        [
            MonthlyAverageCost(
                ingredient_id=prepared.ingredients[0].id,
                month=month,
                avg_cost=Decimal(price),
                total_qty=Decimal(1),
            )
            for month, price in ((202608, 500), (202609, 9000))
        ]
    )
    await session.flush()

    # The voucher is dated September (the frozen clock), the order is August's.
    assert await costing.backfill_issue_costs(session, 202609) == 0
    assert await costing.backfill_issue_costs(session, 202608) == 1
    line = (await session.execute(select(StockIssueLine))).scalar_one()
    await session.refresh(line)
    assert line.estimated_cost == Decimal(1000)


async def test_a_dish_write_off_is_not_added_to_the_waste_cost_nor_the_total(
    api_client, warehouse_token, manager_token, session
):
    prepared = await _prepared(session, servings=3, per_portion="2", average="1500")
    period = month_period("2026-09")
    before = await queries.cost_of_goods_for(session, period)

    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 2)), headers=_auth(warehouse_token)
    )
    after = await queries.cost_of_goods_for(session, period)

    # The ingredients are already inside 05a/05c through the order; 05b stays untouched.
    assert (after.HaoHut, after.TongGiaVon, after.TamTinh) == (
        before.HaoHut,
        before.TongGiaVon,
        before.TamTinh,
    )
    body = (
        await api_client.get(
            "/api/v1/reports/costs", headers=_auth(manager_token), params={"month": "2026-09"}
        )
    ).json()
    assert Decimal(body["MonDaCheBienBiHuy"]) == Decimal(6000)
    assert Decimal(body["HaoHut"]) == 0


async def test_a_dish_write_off_with_no_price_is_not_counted_as_an_uncosted_waste_line(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session)
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    costs = await queries.cost_of_goods_for(session, month_period("2026-09"))

    assert (costs.TamTinh, costs.SoDongChuaTinhGiaVon) == (False, 0)


# --- listing what can still be written off ----------------------------------------------------


async def test_the_kitchen_lists_prepared_lines_with_the_servings_left_and_no_prices(
    api_client, warehouse_token, session
):
    prepared = await _prepared(session, servings=3)
    await _prepared(session, status="Chờ làm")  # not prepared yet: not offered
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    response = await api_client.get(
        f"{BASE}/issues/dish-lines",
        params={"business_date": SEP_10.isoformat()},
        headers=_auth(warehouse_token),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    (item,) = body["items"]
    assert item["MaChiTietOrder"] == prepared.line.id
    assert (item["SoLuong"], item["SoSuatDaHuy"], item["SoSuatConLai"]) == (3, 1, 2)
    assert not {"DonGia", "ThanhTien", "GiaBan"} & set(item)


async def test_a_fully_written_off_line_drops_out_of_the_list(api_client, warehouse_token, session):
    prepared = await _prepared(session, servings=1)
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    body = (
        await api_client.get(
            f"{BASE}/issues/dish-lines",
            params={"business_date": SEP_10.isoformat()},
            headers=_auth(warehouse_token),
        )
    ).json()

    assert body["items"] == []


async def test_cashiers_cannot_list_the_prepared_lines(api_client, cashier_token):
    response = await api_client.get(f"{BASE}/issues/dish-lines", headers=_auth(cashier_token))

    assert response.status_code == 403


async def test_issue_listing_shows_the_source_of_each_voucher(api_client, warehouse_token, session):
    prepared = await _prepared(session)
    await api_client.post(
        WRITE_OFF, json=_body((prepared.line.id, 1)), headers=_auth(warehouse_token)
    )

    body = (await api_client.get(f"{BASE}/issues", headers=_auth(warehouse_token))).json()

    assert [item["NguonXuat"] for item in body["items"]] == [SOURCE]
