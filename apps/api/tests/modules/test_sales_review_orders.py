"""Sales review gaps, order side: bugs, ordering rules, table binding, roles, audit (WP-B)."""

from datetime import timedelta

import pytest
from sqlalchemy import select, update

from app.modules.catalog.models import DiningTable, Dish, DishPriceVersion
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.sales.models import KitchenTicket, Order, OrderLine, TableMoveLog
from app.shared import business_date
from app.shared.audit import SystemAuditLog
from app.shared.enums import VersionStatus
from tests.helpers import FIXED_NOW
from tests.modules.sales_support import (
    add_ingredient_to_recipe,
    api,
    place_order,
    sellable,
    staff,
    table,
)

BASE = "/api/v1/sales"


async def _table_state(session, table_id):
    """(status, serving order) straight from the database, not from the identity map."""
    row = (
        await session.execute(
            select(DiningTable.status, DiningTable.serving_order_id).where(
                DiningTable.id == table_id
            )
        )
    ).one()
    return row.status, row.serving_order_id


async def _lot_quantities(session, lots):
    rows = (
        await session.execute(
            select(IngredientLot.id, IngredientLot.quantity_remaining).where(
                IngredientLot.id.in_([lot.id for lot in lots])
            )
        )
    ).all()
    by_id = {row.id: float(row.quantity_remaining) for row in rows}
    return [by_id[lot.id] for lot in lots]


async def _audits(session, order_id, action=None):
    query = select(SystemAuditLog).where(
        SystemAuditLog.target_entity == "ORDER", SystemAuditLog.target_id == str(order_id)
    )
    if action:
        query = query.where(SystemAuditLog.action == action)
    return list((await session.execute(query.order_by(SystemAuditLog.id))).scalars())


# --- bugs ----------


@pytest.mark.anyio
async def test_cancel_line_succeeds_when_two_or_more_lines_remain(session):
    """cancel_line used scalar_one_or_none() over every remaining line: MultipleResultsFound."""
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1)])
    for _ in range(2):
        added = await client.post(
            f"{BASE}/orders/{order['MaOrder']}/lines",
            json={"MaMon": world.dish.id, "SoLuong": 1},
            headers=cashier,
        )
        assert added.status_code == 201, added.text
    first = order["lines"][0]["MaChiTietOrder"]

    response = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines/{first}/cancel",
        json={"LyDo": "khách đổi ý"},
        headers=cashier,
    )

    assert response.status_code == 200, response.text
    live = (
        await session.execute(
            select(OrderLine).where(
                OrderLine.order_id == order["MaOrder"], OrderLine.status != "Đã hủy"
            )
        )
    ).scalars()
    assert len(list(live)) == 2


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("patch", "/orders/{o2}/lines/{l1}", {"SoLuong": 3}),
        ("patch", "/orders/{o2}/lines/{l1}/status", {"TrangThai": "Đã xác nhận xong"}),
        ("post", "/orders/{o2}/lines/{l1}/cancel", {"LyDo": "x"}),
    ],
)
async def test_a_line_of_another_order_is_not_reachable_through_this_order(
    session, method, path, body
):
    """IDOR: the line id in the URL must belong to the order id in the URL."""
    world = await sellable(session)
    desk_a, desk_b = await table(session, "A"), await table(session, "B")
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    first = await place_order(client, cashier, desk_a, [(world.dish.id, 1)])
    second = await place_order(client, cashier, desk_b, [(world.dish.id, 1)])
    url = path.format(o2=second["MaOrder"], l1=first["lines"][0]["MaChiTietOrder"])

    response = await getattr(client, method)(f"{BASE}{url}", json=body, headers=cashier)

    assert response.status_code == 404
    line = await session.get(OrderLine, first["lines"][0]["MaChiTietOrder"])
    await session.refresh(line)
    assert (line.status, line.quantity) == ("Chờ làm", 1)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("path", "method", "body"),
    [
        ("/orders/{o}/lines", "post", {"MaMon": 1, "SoLuong": 0}),
        ("/orders/{o}/lines", "post", {"MaMon": 1, "SoLuong": -2}),
        ("/orders/{o}/lines", "post", {"SoLuong": 1}),
        ("/orders/{o}/lines", "post", {"MaMon": "abc", "SoLuong": 1}),
        ("/orders/{o}/lines/{l}", "patch", {"SoLuong": 0}),
        ("/orders/{o}/lines/{l}", "patch", {}),
        ("/orders/{o}/lines/{l}/status", "patch", {}),
        ("/orders/{o}/lines/{l}/cancel", "post", {}),
        ("/orders/{o}/lines/{l}/cancel", "post", {"LyDo": ""}),
        ("/orders/{o}/move", "post", {}),
        ("/orders/{o}/move", "post", {"MaBanDich": 0}),
        ("/orders/{o}/cancel", "post", {}),
        ("/orders/{o}/cancel", "post", {"LyDoHuy": "x" * 300}),
    ],
)
async def test_request_bodies_are_validated_models(session, path, method, body):
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    manager, _ = await staff(session, "MANAGER", "m1")
    order = await place_order(client, manager, desk, [(world.dish.id, 1)])
    url = path.format(o=order["MaOrder"], l=order["lines"][0]["MaChiTietOrder"])

    response = await getattr(client, method)(f"{BASE}{url}", json=body, headers=manager)

    assert response.status_code == 422, response.text


@pytest.mark.anyio
async def test_add_line_is_priced_by_the_version_effective_now_not_the_order_date(session):
    world = await sellable(session, price=50000)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1)])
    # The order was opened on an earlier Business Date; the price was changed since.
    yesterday = business_date.business_date_of(business_date.now()) - timedelta(days=1)
    await session.execute(
        update(Order).where(Order.id == order["MaOrder"]).values(business_date=yesterday)
    )
    await session.execute(
        update(DishPriceVersion)
        .where(DishPriceVersion.dish_id == world.dish.id)
        .values(price=60000)
    )
    await session.commit()

    added = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines",
        json={"MaMon": world.dish.id, "SoLuong": 1},
        headers=cashier,
    )

    assert added.status_code == 201, added.text
    assert added.json()["DonGia"] == 60000
    movement = (
        await session.execute(
            select(StockMovement).where(
                StockMovement.order_line_id == added.json()["MaChiTietOrder"]
            )
        )
    ).scalar_one()
    assert movement.business_date == business_date.business_date_of(business_date.now())


@pytest.mark.anyio
async def test_reducing_then_cancelling_returns_each_lot_what_it_gave(session):
    """The return is keyed by lot: a draw spread over two lots goes back to the same two lots."""
    now = business_date.now()
    world = await sellable(
        session,
        per_portion=3,
        lots=[(2, now - timedelta(days=2), None), (7, now - timedelta(days=1), None)],
    )
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, desk, [(world.dish.id, 2)])  # 6 = 2 + 4
    line_id = order["lines"][0]["MaChiTietOrder"]
    assert await _lot_quantities(session, world.lots) == [0, 3]

    reduced = await client.patch(
        f"{BASE}/orders/{order['MaOrder']}/lines/{line_id}", json={"SoLuong": 1}, headers=cashier
    )
    assert reduced.status_code == 200, reduced.text
    cancelled = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines/{line_id}/cancel",
        json={"LyDo": "đổi món"},
        headers=cashier,
    )
    assert cancelled.status_code == 200, cancelled.text

    assert await _lot_quantities(session, world.lots) == [2, 7]
    movements = list(
        (
            await session.execute(select(StockMovement).where(StockMovement.kind == "Hoàn kho"))
        ).scalars()
    )
    assert movements and all(m.order_line_id == line_id for m in movements)
    assert sum(float(m.qty) for m in movements) == 6


@pytest.mark.anyio
async def test_a_return_with_two_ingredients_is_not_confused_by_lot_ids_equal_to_ingredient_ids(
    session,
):
    """The old return tracked 'already returned' by ingredient id and then by lot id in the
    same dict, so lot 2 of ingredient 1 shadowed ingredient 2 and under-returned it."""
    now = business_date.now()
    world = await sellable(
        session, per_portion=2, lots=[(1, now - timedelta(days=2), None), (5, now, None)]
    )
    other, other_lot = await add_ingredient_to_recipe(session, world, per_portion=3, quantity=10)
    assert (world.ingredient.id, world.lots[1].id, other.id) == (1, 2, 2)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    keep = await sellable(session, name="Món giữ bàn")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1), (keep.dish.id, 1)])

    cancelled = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines/{order['lines'][0]['MaChiTietOrder']}/cancel",
        json={"LyDo": "khách đổi ý"},
        headers=cashier,
    )

    assert cancelled.status_code == 200, cancelled.text
    assert await _lot_quantities(session, [*world.lots, other_lot]) == [1, 5, 10]


@pytest.mark.anyio
async def test_cancelling_a_line_makes_the_dish_orderable_again(session):
    """_return_line_stock must recompute the derived out-of-stock flag."""
    world = await sellable(session, lots=[(1, business_date.now(), None)])
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    other = await sellable(session, name="Món phụ")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1), (other.dish.id, 1)])
    dish = await session.get(Dish, world.dish.id)
    await session.refresh(dish)
    assert dish.out_of_stock is True

    cancelled = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines/{order['lines'][0]['MaChiTietOrder']}/cancel",
        json={"LyDo": "khách đổi ý"},
        headers=cashier,
    )

    assert cancelled.status_code == 200, cancelled.text
    await session.refresh(dish)
    assert dish.out_of_stock is False


# --- ordering enforcement ----------


async def _orderable_probe(session, mutate):
    world = await sellable(session)
    await mutate(session, world)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    response = await client.post(
        f"{BASE}/orders",
        json={"MaBan": desk.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )
    return response, desk


async def _delete(session, world):
    await session.execute(update(Dish).where(Dish.id == world.dish.id).values(is_deleted=True))
    await session.commit()


async def _draft(session, world):
    await session.execute(update(Dish).where(Dish.id == world.dish.id).values(missing_recipe=True))
    await session.commit()


async def _pause(session, world):
    await session.execute(update(Dish).where(Dish.id == world.dish.id).values(manually_paused=True))
    await session.commit()


async def _no_price(session, world):
    await session.execute(
        update(DishPriceVersion)
        .where(DishPriceVersion.dish_id == world.dish.id)
        .values(status=VersionStatus.HET_HIEU_LUC.value)
    )
    await session.commit()


@pytest.mark.anyio
@pytest.mark.parametrize("mutate", [_delete, _draft, _pause, _no_price])
async def test_a_dish_that_cannot_be_sold_is_refused_and_nothing_is_written(session, mutate):
    response, desk = await _orderable_probe(session, mutate)

    assert response.status_code == 422, response.text
    assert (await session.execute(select(Order))).first() is None
    assert (await session.get(DiningTable, desk.id)).status == "Trống"


@pytest.mark.anyio
async def test_a_dish_without_a_recipe_version_is_refused(session):
    world = await sellable(session, with_recipe=False)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")

    response = await client.post(
        f"{BASE}/orders",
        json={"MaBan": desk.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )

    assert response.status_code == 422
    assert (await session.execute(select(Order))).first() is None


@pytest.mark.anyio
async def test_a_dish_out_of_ingredients_is_refused_even_if_the_cached_flag_is_stale(session):
    world = await sellable(session, lots=[(0.5, business_date.now(), None)])
    await session.execute(update(Dish).where(Dish.id == world.dish.id).values(out_of_stock=False))
    await session.commit()
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")

    response = await client.post(
        f"{BASE}/orders",
        json={"MaBan": desk.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )

    assert response.status_code == 422
    assert "hết nguyên liệu" in response.json()["error"]["message"]


@pytest.mark.anyio
async def test_expired_lots_never_count_as_available(session):
    today = business_date.business_date_of(business_date.now())
    world = await sellable(
        session,
        lots=[
            (50, business_date.now() - timedelta(days=9), today - timedelta(days=2)),
            (1, business_date.now(), None),
        ],
    )
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")

    too_many = await client.post(
        f"{BASE}/orders",
        json={"MaBan": desk.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 2}]},
        headers=cashier,
    )
    enough = await client.post(
        f"{BASE}/orders",
        json={"MaBan": desk.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )

    assert too_many.status_code == 422
    assert enough.status_code == 201, enough.text
    assert await _lot_quantities(session, world.lots) == [50, 0]


@pytest.mark.anyio
async def test_one_unsellable_line_refuses_the_whole_order(session):
    good = await sellable(session, name="Còn")
    bad = await sellable(session, name="Hết", lots=[(0.5, business_date.now(), None)])
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")

    response = await client.post(
        f"{BASE}/orders",
        json={
            "MaBan": desk.id,
            "lines": [{"MaMon": good.dish.id, "SoLuong": 1}, {"MaMon": bad.dish.id, "SoLuong": 1}],
        },
        headers=cashier,
    )

    assert response.status_code == 422
    assert (await session.execute(select(Order))).first() is None
    assert await _lot_quantities(session, good.lots) == [20]


@pytest.mark.anyio
async def test_dine_in_needs_a_free_table_and_marks_it_as_serving(session):
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")

    first = await place_order(client, cashier, desk, [(world.dish.id, 1)])
    second = await client.post(
        f"{BASE}/orders",
        json={"MaBan": desk.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )

    assert await _table_state(session, desk.id) == ("Đang phục vụ", first["MaOrder"])
    assert second.status_code == 422
    assert len(list((await session.execute(select(Order))).scalars())) == 1


@pytest.mark.anyio
async def test_dine_in_without_a_table_and_a_deleted_table_are_refused(session):
    world = await sellable(session)
    gone = await table(session, "Đã xóa")
    gone.is_deleted = True
    await session.commit()
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")

    no_table = await client.post(
        f"{BASE}/orders",
        json={"LoaiDon": "Tại chỗ", "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )
    deleted = await client.post(
        f"{BASE}/orders",
        json={"MaBan": gone.id, "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )
    takeaway = await client.post(
        f"{BASE}/orders",
        json={"LoaiDon": "Mang về", "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
        headers=cashier,
    )

    assert no_table.status_code == 422 and deleted.status_code == 422
    assert takeaway.status_code == 201 and takeaway.json()["MaBan"] is None


@pytest.mark.anyio
async def test_moving_a_table_rebinds_the_serving_order_and_is_audited(session):
    world = await sellable(session)
    source, target = await table(session, "Nguồn"), await table(session, "Đích")
    client = await api(session)
    cashier, cashier_user = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, source, [(world.dish.id, 1)])

    response = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/move", json={"MaBanDich": target.id}, headers=cashier
    )

    assert response.status_code == 200, response.text
    assert await _table_state(session, source.id) == ("Trống", None)
    assert await _table_state(session, target.id) == ("Đang phục vụ", order["MaOrder"])
    log = (await session.execute(select(TableMoveLog))).scalar_one()
    assert log.performed_by == cashier_user.id and log.created_at == FIXED_NOW
    audit = (await _audits(session, order["MaOrder"], "MOVE_ORDER_TABLE"))[0]
    assert audit.before == {"MaBan": source.id} and audit.after == {"MaBan": target.id}


@pytest.mark.anyio
async def test_a_released_table_cannot_receive_a_late_move_or_add_on(session):
    world = await sellable(session)
    source, target = await table(session, "Nguồn"), await table(session, "Đích")
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, source, [(world.dish.id, 1)])
    released = await client.post(f"/api/v1/catalog/tables/{source.id}/release", headers=cashier)
    assert released.status_code == 200, released.text

    move = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/move", json={"MaBanDich": target.id}, headers=cashier
    )
    add = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines",
        json={"MaMon": world.dish.id, "SoLuong": 1},
        headers=cashier,
    )

    assert move.status_code == 422 and add.status_code == 422


@pytest.mark.anyio
async def test_a_takeaway_order_cannot_be_extended_or_moved(session):
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    order = (
        await client.post(
            f"{BASE}/orders",
            json={"LoaiDon": "Mang về", "lines": [{"MaMon": world.dish.id, "SoLuong": 1}]},
            headers=cashier,
        )
    ).json()

    add = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines",
        json={"MaMon": world.dish.id, "SoLuong": 1},
        headers=cashier,
    )
    move = await client.post(
        f"{BASE}/orders/{order['MaOrder']}/move", json={"MaBanDich": desk.id}, headers=cashier
    )

    assert add.status_code == 422 and move.status_code == 422


@pytest.mark.anyio
async def test_cancelling_a_whole_order_frees_the_table_only_when_the_guests_left(session):
    world = await sellable(session)
    stays, leaves = await table(session, "Ở lại"), await table(session, "Đã đi")
    client = await api(session)
    manager, _ = await staff(session, "MANAGER", "m1")
    first = await place_order(client, manager, stays, [(world.dish.id, 1)])
    second = await place_order(client, manager, leaves, [(world.dish.id, 1)])

    await client.post(
        f"{BASE}/orders/{first['MaOrder']}/cancel", json={"LyDoHuy": "a"}, headers=manager
    )
    await client.post(
        f"{BASE}/orders/{second['MaOrder']}/cancel",
        json={"LyDoHuy": "b", "KhachDaRoiDi": True},
        headers=manager,
    )

    assert await _table_state(session, stays.id) == ("Đang phục vụ", first["MaOrder"])
    assert await _table_state(session, leaves.id) == ("Trống", None)


# --- selection submit is all-or-nothing ----------


@pytest.mark.anyio
async def test_selection_submit_with_one_changed_dish_creates_nothing(session):
    steady = await sellable(session, name="Giữ nguyên")
    changing = await sellable(session, name="Đổi giá")
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    created = await client.post(f"{BASE}/selections", json={}, headers=cashier)
    selection = created.json()["MaLuotChon"]
    for dish in (steady.dish, changing.dish):
        held = await client.put(
            f"{BASE}/selections/{selection}/lines/{dish.id}",
            json={"SoLuong": 1, "MaBan": desk.id},
            headers=cashier,
        )
        assert held.status_code == 200, held.text
    await session.execute(
        update(DishPriceVersion)
        .where(DishPriceVersion.dish_id == changing.dish.id)
        .values(status=VersionStatus.HET_HIEU_LUC.value)
    )
    session.add(
        DishPriceVersion(
            dish_id=changing.dish.id,
            price=99000,
            business_date=business_date.business_date_of(business_date.now()),
            status=VersionStatus.HIEU_LUC.value,
            change_type="Sửa trực tiếp",
        )
    )
    await session.commit()

    response = await client.post(
        f"{BASE}/selections/{selection}/submit", json={"MaYeuCauGui": "req-1"}, headers=cashier
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["CanXacNhanLai"] is True and body["MaOrder"] is None and body["lines"] == []
    assert (await session.execute(select(Order))).first() is None
    assert (await session.get(DiningTable, desk.id)).status == "Trống"
    assert await _lot_quantities(session, steady.lots) == [20]


@pytest.mark.anyio
async def test_a_paused_dish_cannot_be_held_or_sent(session):
    world = await sellable(session)
    await session.execute(update(Dish).where(Dish.id == world.dish.id).values(manually_paused=True))
    await session.commit()
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    selection = (await client.post(f"{BASE}/selections", json={}, headers=cashier)).json()[
        "MaLuotChon"
    ]

    held = await client.put(
        f"{BASE}/selections/{selection}/lines/{world.dish.id}",
        json={"SoLuong": 1, "MaBan": desk.id},
        headers=cashier,
    )

    assert held.status_code == 422


# --- roles, audit, tickets, clock ----------


@pytest.mark.anyio
@pytest.mark.parametrize(
    "path",
    [
        "/floor",
        "/orders",
        "/orders/1",
        "/orders/1/tickets",
        "/orders/1/payments",
        "/orders/1/invoice",
        "/orders/1/provisional-bill",
    ],
)
async def test_the_kitchen_role_cannot_read_sales_data(session, path):
    client = await api(session)
    kitchen, _ = await staff(session, "WAREHOUSE", "k1")

    response = await client.get(f"{BASE}{path}", headers=kitchen)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_every_sales_route_but_the_gateway_webhooks_requires_a_role():
    from app.main import app

    unguarded = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if not path.startswith("/api/v1/sales") or "/webhooks/" in path:
            continue
        guards = [
            dep.call
            for dep in route.dependant.dependencies
            if getattr(dep.call, "__name__", "") == "_guard"
        ]
        if not guards:
            unguarded.append(path)
    assert unguarded == []


@pytest.mark.anyio
async def test_the_webhooks_are_the_only_unauthenticated_sales_routes(session):
    client = await api(session)
    for path in ("/webhooks/payment", "/webhooks/sepay"):
        response = await client.post(f"{BASE}{path}", json={})
        assert response.status_code != 403  # reachable without a login (gateway auth decides)


@pytest.mark.anyio
async def test_order_mutations_write_order_audit_rows_with_before_and_after(session):
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, user = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, desk, [(world.dish.id, 2)])
    line_id = order["lines"][0]["MaChiTietOrder"]
    await client.patch(
        f"{BASE}/orders/{order['MaOrder']}/lines/{line_id}", json={"SoLuong": 1}, headers=cashier
    )
    await client.post(
        f"{BASE}/orders/{order['MaOrder']}/lines/{line_id}/cancel",
        json={"LyDo": "khách đổi ý"},
        headers=cashier,
    )

    rows = await _audits(session, order["MaOrder"])

    actions = [row.action for row in rows]
    assert actions[:3] == ["SUBMIT_ORDER", "UPDATE_ORDER_LINE", "CANCEL_ORDER_LINE"]
    assert all(row.user_id == user.id and row.occurred_at == FIXED_NOW for row in rows)
    update_row = rows[1]
    assert update_row.before["SoLuong"] == 2 and update_row.after["SoLuong"] == 1
    cancel_row = rows[2]
    assert cancel_row.reason == "khách đổi ý" and cancel_row.after["TrangThai"] == "Đã hủy"


@pytest.mark.anyio
async def test_the_kitchen_ticket_names_the_table_and_the_dishes(session):
    world = await sellable(session, name="Phở bò")
    desk = await table(session, "Bàn 07")
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    await place_order(client, cashier, desk, [(world.dish.id, 2)])

    ticket = (await session.execute(select(KitchenTicket))).scalar_one()

    assert "Bàn 07" in ticket.content and "Phở bò x2" in ticket.content
    assert ticket.created_at == FIXED_NOW


@pytest.mark.anyio
async def test_timestamps_come_from_the_application_clock(session):
    world = await sellable(session)
    desk = await table(session)
    client = await api(session)
    cashier, _ = await staff(session, "CASHIER", "c1")
    order = await place_order(client, cashier, desk, [(world.dish.id, 1)])

    row = await session.get(Order, order["MaOrder"])
    line = await session.get(OrderLine, order["lines"][0]["MaChiTietOrder"])

    assert row.created_at == FIXED_NOW and line.added_at == FIXED_NOW
