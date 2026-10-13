"""FR-REP-02, FR-REP-05c, FR-REP-08, FR-REP-10 as the report words them."""

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from app.modules.inventory.models import StockMovement
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import OrderStatus
from tests.helpers import FIXED_NOW
from tests.modules.conftest import (
    _r_dish,
    _r_ingredient,
    _r_invoice,
    _r_line,
    _r_order,
    _r_recipe,
)

COMPARISON = "/api/v1/reports/comparison"
CANCELLED = "/api/v1/reports/cancelled-orders"
UNSETTLED = "/api/v1/reports/unsettled"
COSTS = "/api/v1/reports/costs"
NO_PERCENTAGE = "Không xác định tỷ lệ phần trăm"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _paid_order(session, bd: date, dish, quantity: int, price: int, recipe=None):
    order = await _r_order(session, bd=bd, status="Đã thanh toán", order_type="Mang về")
    await _r_line(session, order, dish, quantity, price, recipe_id=recipe.id if recipe else None)
    await _r_invoice(session, order, bd=bd, total=quantity * price)
    return order


# --- FR-REP-08: two periods, revenue and cost -----------------------------------------------


async def test_comparison_reports_revenue_and_cost_with_absolute_and_percent_change(
    api_client, manager_token, session
):
    dish = await _r_dish(session, "Phở")
    flour = await _r_ingredient(session, "Bột", 100, month=202608)
    await _r_ingredient(session, "Bột phụ", 1)  # a second ingredient must not leak in
    recipe = await _r_recipe(session, dish, flour, 2, date(2026, 8, 1))
    await _paid_order(session, date(2026, 8, 10), dish, 2, 50000, recipe)  # 100000, cost 400
    await _paid_order(session, date(2026, 9, 10), dish, 3, 50000)  # 150000, no recipe -> cost 0
    await session.commit()

    body = (
        await api_client.get(
            COMPARISON, headers=_auth(manager_token), params={"left": "2026-08", "right": "2026-09"}
        )
    ).json()

    assert Decimal(body["left"]["GiaVon"]) == Decimal("400")
    assert Decimal(body["right"]["GiaVon"]) == 0
    assert Decimal(body["doanh_thu"]["ChenhLechTuyetDoi"]) == Decimal("50000")
    assert Decimal(body["doanh_thu"]["PhanTramChenhLech"]) == Decimal("50.00")
    assert body["doanh_thu"]["GhiChu"] is None
    assert Decimal(body["chi_phi"]["ChenhLechTuyetDoi"]) == Decimal("-400")
    assert Decimal(body["chi_phi"]["PhanTramChenhLech"]) == Decimal("-100.00")
    assert Decimal(body["change_percent"]) == Decimal("50.00")


async def test_an_empty_baseline_gives_only_the_absolute_difference_and_the_note(
    api_client, manager_token, session
):
    dish = await _r_dish(session, "Bún")
    await _paid_order(session, date(2026, 9, 10), dish, 1, 70000)
    await session.commit()

    body = (
        await api_client.get(
            COMPARISON, headers=_auth(manager_token), params={"left": "2026-08", "right": "2026-09"}
        )
    ).json()

    assert Decimal(body["doanh_thu"]["ChenhLechTuyetDoi"]) == Decimal("70000")
    assert body["doanh_thu"]["PhanTramChenhLech"] is None
    assert body["doanh_thu"]["GhiChu"] == NO_PERCENTAGE
    assert body["chi_phi"]["PhanTramChenhLech"] is None
    assert body["chi_phi"]["GhiChu"] == NO_PERCENTAGE
    assert body["change_percent"] is None


async def test_any_two_periods_can_be_compared(api_client, manager_token, session):
    dish = await _r_dish(session, "Cơm")
    await _paid_order(session, date(2026, 9, 1), dish, 1, 10000)
    await _paid_order(session, date(2026, 9, 2), dish, 1, 10000)
    await _paid_order(session, date(2026, 9, 8), dish, 3, 10000)
    await session.commit()

    body = (
        await api_client.get(
            COMPARISON,
            headers=_auth(manager_token),
            params={"left": "2026-09-01..2026-09-07", "right": "2026-09-08..2026-09-14"},
        )
    ).json()

    assert Decimal(body["left"]["DoanhThu"]) == 20000
    assert Decimal(body["right"]["DoanhThu"]) == 30000
    assert Decimal(body["doanh_thu"]["PhanTramChenhLech"]) == Decimal("50.00")


@pytest.mark.parametrize("bad", ["2026-09-07..2026-09-01", "2026-09-01..soon", "..", "2026"])
async def test_a_malformed_period_is_a_business_error(api_client, manager_token, bad):
    response = await api_client.get(
        COMPARISON, headers=_auth(manager_token), params={"left": bad, "right": "2026-09"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_RULE_VIOLATION"


# --- FR-REP-10: cancelled and closed-unpaid orders -----------------------------------------


async def _closed_unpaid(session, bd: date, dish, quantity: int, price: int, recipe, ingredient):
    order = await _r_order(
        session, bd=bd, status=OrderStatus.DONG_CHUA_THU_DUOC_TIEN.value, order_type="Mang về"
    )
    order.closed_at = datetime(bd.year, bd.month, bd.day, 22, 15)
    line = await _r_line(session, order, dish, quantity, price, recipe_id=recipe.id)
    session.add(
        StockMovement(
            ingredient_id=ingredient.id,
            kind="Trừ tự động",
            qty=Decimal(-quantity),
            business_date=bd,
            order_line_id=line.id,
        )
    )
    session.add(
        SystemAuditLog(
            user_id=1,
            action="CLOSE_ORDER_UNPAID",
            target_entity="ORDER",
            target_id=str(order.id),
            reason="Khách bỏ về, không liên lạc được",
        )
    )
    await session.flush()
    return order


async def test_the_cancelled_report_follows_a_day_a_week_or_a_month(
    api_client, manager_token, session
):
    await _r_order(session, bd=date(2026, 9, 3), status="Đã hủy", reason="a", order_type="Mang về")
    await _r_order(session, bd=date(2026, 9, 9), status="Đã hủy", reason="b", order_type="Mang về")
    await _r_order(session, bd=date(2026, 9, 24), status="Đã hủy", reason="c", order_type="Mang về")
    await session.commit()

    async def count(**params) -> int:
        body = (await api_client.get(CANCELLED, headers=_auth(manager_token), params=params)).json()
        return body["SoLuong"]

    assert await count(granularity="day", anchor="2026-09-09") == 1
    assert await count(granularity="week", anchor="2026-09-09") == 1  # Mon 7 - Sun 13
    assert await count(granularity="week", anchor="2026-09-03") == 1  # Mon 31 Aug - Sun 6
    assert await count(granularity="month", anchor="2026-09-01") == 3
    assert await count(month="2026-09") == 3
    assert await count(month="2026-08") == 0


async def test_orders_closed_unpaid_form_their_own_group_with_cost_and_who_closed_them(
    api_client, manager_token, session
):
    dish = await _r_dish(session, "Lẩu")
    flour = await _r_ingredient(session, "Nấm", 200)
    recipe = await _r_recipe(session, dish, flour, 2, date(2026, 9, 1))
    order = await _closed_unpaid(session, date(2026, 9, 12), dish, 3, 90000, recipe, flour)
    await _r_order(
        session, bd=date(2026, 9, 12), status="Đã hủy", reason="nhầm bàn", order_type="Mang về"
    )
    await session.commit()

    body = (
        await api_client.get(CANCELLED, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert body["SoLuong"] == 1  # the cancelled group is not polluted
    group = body["DongChuaThuDuocTien"]
    assert group["SoLuong"] == 1
    assert Decimal(group["TongSoTienChuaThu"]) == Decimal("270000")
    assert Decimal(group["TongGiaVonDaTieuHao"]) == Decimal("600")  # 3 servings x 1 x 200
    row = group["items"][0]
    assert (row["MaOrder"], row["LyDo"], row["NguoiDong"]) == (
        order.id,
        "Khách bỏ về, không liên lạc được",
        1,
    )
    assert row["ThoiDiemDong"].startswith("2026-09-12T22:15")
    # Never summed into one "loss" figure, never revenue.
    assert Decimal(body["TongGiaTri"]) == 0
    revenue = (
        await api_client.get(
            "/api/v1/reports/revenue", headers=_auth(manager_token), params={"month": "2026-09"}
        )
    ).json()
    assert Decimal(revenue["total"]) == 0


# --- FR-REP-05c: what lost orders consumed -----------------------------------------------


async def test_lost_orders_cost_what_they_consumed_and_did_not_give_back(
    api_client, manager_token, session
):
    dish = await _r_dish(session, "Gà")
    chicken = await _r_ingredient(session, "Thịt gà", 1000)
    recipe = await _r_recipe(session, dish, chicken, 1, date(2026, 9, 1))
    cancelled = await _r_order(
        session, bd=date(2026, 9, 5), status="Đã hủy", reason="x", order_type="Mang về"
    )
    line = await _r_line(session, cancelled, dish, 2, 100000, status="Đã hủy", recipe_id=recipe.id)
    session.add_all(
        [
            StockMovement(
                ingredient_id=chicken.id,
                kind="Trừ tự động",
                qty=Decimal(-2),
                business_date=date(2026, 9, 5),
                order_line_id=line.id,
            ),
            StockMovement(
                ingredient_id=chicken.id,
                kind="Hoàn kho",
                qty=Decimal(1),
                business_date=date(2026, 9, 5),
                order_line_id=line.id,
            ),
        ]
    )
    await session.commit()

    body = (
        await api_client.get(COSTS, headers=_auth(manager_token), params={"month": "2026-09"})
    ).json()

    assert Decimal(body["TieuHaoOrderHuy"]) == Decimal("1000")  # one serving was never returned
    assert Decimal(body["TongGiaVon"]) == Decimal("1000")


# --- FR-REP-02: waiting for verification ----------------------------------------------------


async def test_unsettled_orders_are_listed_apart_with_value_and_waiting_time(
    api_client, manager_token, session, monkeypatch
):
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW)
    dish = await _r_dish(session, "Chè")
    waiting = await _r_order(
        session,
        bd=date(2026, 9, 24),
        status="Chờ xác minh thanh toán",
        order_type="Mang về",
        at=FIXED_NOW - timedelta(minutes=45),
    )
    waiting.updated_at = FIXED_NOW - timedelta(minutes=30)
    await _r_line(session, waiting, dish, 2, 25000)
    await _r_line(session, waiting, dish, 1, 25000, status="Đã hủy")
    await _r_order(session, bd=date(2026, 9, 24), status="Đang mở", order_type="Mang về")
    session.add(
        SystemAuditLog(
            user_id=2,
            action="MARK_PAYMENT_FOR_VERIFICATION",
            target_entity="ORDER",
            target_id=str(waiting.id),
            reason="Khách báo đã chuyển khoản",
        )
    )
    await session.commit()

    body = (await api_client.get(UNSETTLED, headers=_auth(manager_token))).json()

    assert body["SoLuong"] == 1
    assert Decimal(body["TongGiaTri"]) == Decimal("50000")
    row = body["items"][0]
    assert (row["MaOrder"], row["SoPhutDaCho"]) == (waiting.id, 30)
    assert row["KetQuaXuLyGanNhat"] == "Khách báo đã chuyển khoản"


async def test_an_order_waiting_for_verification_is_not_counted_as_sold(
    api_client, manager_token, session
):
    dish = await _r_dish(session, "Bánh")
    waiting = await _r_order(
        session, bd=date(2026, 9, 10), status="Chờ xác minh thanh toán", order_type="Mang về"
    )
    await _r_line(session, waiting, dish, 5, 10000)
    await _paid_order(session, date(2026, 9, 10), dish, 1, 10000)
    await session.commit()

    ranking = (
        await api_client.get(
            "/api/v1/reports/dishes", headers=_auth(manager_token), params={"month": "2026-09"}
        )
    ).json()

    assert [row["SoLuong"] for row in ranking["items"]] == [1]


async def test_the_new_report_views_are_manager_only(api_client, cashier_token, warehouse_token):
    for token in (cashier_token, warehouse_token):
        for path in (UNSETTLED, CANCELLED, COMPARISON):
            response = await api_client.get(
                path, headers=_auth(token), params={"left": "2026-08", "right": "2026-09"}
            )
            assert response.status_code == 403, path
