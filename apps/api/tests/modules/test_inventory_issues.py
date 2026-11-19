"""FR-INV-05/06 — manual stock issues, FIFO draw."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import create_access_token, hash_password
from app.main import app
from app.modules.catalog.models import Ingredient
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data
from app.shared import business_date
from tests.helpers import lot_total, movements_for


async def _make_client(session):
    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _headers(session, role="WAREHOUSE", username="kho02"):
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


async def _ingredient(session, name="Thịt bò", stock_qty=0):
    ing = Ingredient(name=name, unit="kg", min_stock=0, stock_qty=stock_qty, is_deleted=False)
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


async def _receipt(session, client, headers, ing, qty, unit_price=1000):
    r = await client.post(
        "/api/v1/inventory/receipts",
        json={"lines": [{"ingredient_id": ing.id, "quantity": qty, "unit_price": unit_price}]},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["MaPhieuNhap"]


@pytest.mark.anyio
async def test_manual_issue_decreases_stock(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 10)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 4}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 6
    assert await lot_total(session, ing.id) == 6


@pytest.mark.anyio
async def test_manual_issue_draws_oldest_lot_first(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5, unit_price=1000)
    await _receipt(session, client, h, ing, 5, unit_price=2000)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 3}]},
        headers=h,
    )
    assert r.status_code == 201, r.text
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    lots = (
        (await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == ing.id)))
        .scalars()
        .all()
    )
    lots.sort(key=lambda x: x.received_at)
    assert float(lots[0].quantity_remaining) == 2  # first lot drawn down 5 -> 2
    assert float(lots[1].quantity_remaining) == 5  # second lot untouched


@pytest.mark.anyio
async def test_manual_issue_refused_when_it_would_go_negative(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 2)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 5}]},
        headers=h,
    )
    assert r.status_code == 422
    await session.refresh(ing)
    assert float(ing.stock_qty) == 2


@pytest.mark.anyio
async def test_manual_issue_records_ledger_movement(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hỏng", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    moves = await movements_for(session, ing.id)
    kinds = [m["LoaiGiaoDich"] for m in moves]
    assert "Xuất thủ công" in kinds


@pytest.mark.anyio
async def test_list_issues(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    r = await client.get("/api/v1/inventory/issues", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["LyDo"] == "Hao hụt"


@pytest.mark.anyio
async def test_the_issue_source_is_a_column_not_a_note(session):
    """FR-INV-05: NguonXuat carries the source; GhiChu stays free for a genuine note."""
    from app.modules.inventory.models import StockIssue

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    created = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    assert created.status_code == 201, created.text
    issue = await session.get(StockIssue, created.json()["MaPhieuXuat"])
    assert issue.source == "Nguyên liệu"
    assert issue.note is None
    listed = (await client.get("/api/v1/inventory/issues", headers=h)).json()["items"][0]
    assert listed["Nguon"] == "Nguyên liệu"
    detail = await client.get(f"/api/v1/inventory/issues/{issue.id}", headers=h)
    assert detail.json()["Nguon"] == "Nguyên liệu"


@pytest.mark.anyio
async def test_list_issues_filters_by_reason_and_date_range(session):
    from datetime import date, timedelta

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )
    await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hỏng", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=h,
    )

    by_reason = await client.get("/api/v1/inventory/issues?reason=Hỏng", headers=h)
    assert by_reason.status_code == 200
    assert by_reason.json()["total"] == 1
    assert by_reason.json()["items"][0]["LyDo"] == "Hỏng"

    tomorrow = date.today() + timedelta(days=1)
    out_of_range = await client.get(
        f"/api/v1/inventory/issues?date_from={tomorrow.isoformat()}&date_to={tomorrow.isoformat()}",
        headers=h,
    )
    assert out_of_range.json()["total"] == 0


@pytest.mark.anyio
async def test_list_issues_rejects_a_malformed_date(session):
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.get("/api/v1/inventory/issues?date_from=25-09-2026", headers=h)
    assert r.status_code == 422


@pytest.mark.anyio
async def test_list_issues_total_reflects_all_rows_across_pages(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 10)
    for _ in range(3):
        await client.post(
            "/api/v1/inventory/issues",
            json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
            headers=h,
        )
    r = await client.get("/api/v1/inventory/issues?page=1&page_size=2", headers=h)
    body = r.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2


@pytest.mark.anyio
async def test_issue_can_draw_from_a_selected_lot(session):
    """FR-INV-05/BR-LOT-01: the operator may choose which lot to write off."""
    from sqlalchemy import select

    from app.modules.inventory.models import IngredientLot

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 4)
    first_lot = (
        (await session.execute(select(IngredientLot).where(IngredientLot.ingredient_id == ing.id)))
        .scalars()
        .first()
    )
    await _receipt(session, client, h, ing, 6)
    lots = (
        (
            await session.execute(
                select(IngredientLot)
                .where(IngredientLot.ingredient_id == ing.id)
                .order_by(IngredientLot.id)
            )
        )
        .scalars()
        .all()
    )
    later_lot = lots[-1]

    r = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Hết hạn",
            "source": "Nguyên liệu",
            "lines": [{"ingredient_id": ing.id, "quantity": 3, "lot_id": later_lot.id}],
        },
        headers=h,
    )

    assert r.status_code == 201, r.text
    await session.refresh(first_lot)
    await session.refresh(later_lot)
    assert float(first_lot.quantity_remaining) == 4
    assert float(later_lot.quantity_remaining) == 3


@pytest.mark.anyio
async def test_prepared_dish_issue_only_classifies_cost(session):
    """FR-INV-05: source "Món đã chế biến" must not subtract stock again."""
    from app.modules.catalog.models import Dish, DishGroup
    from app.modules.inventory.models import StockMovement
    from app.modules.sales.models import Order, OrderLine

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 10)
    group = DishGroup(name="Món", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Phở", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    order = Order(business_date=business_date.now().date(), table_id=None, order_type="Mang về")
    session.add(order)
    await session.flush()
    line = OrderLine(
        order_id=order.id,
        dish_id=dish.id,
        quantity=2,
        unit_price=50000,
        status="Đã phục vụ",
    )
    session.add(line)
    await session.flush()
    # The original send drew 4 units for 2 servings; the write-off must derive from
    # that ledger, not from a recipe the user could type.
    session.add(
        StockMovement(
            ingredient_id=ing.id,
            kind="Trừ tự động",
            qty=-4,
            business_date=business_date.business_date_of(business_date.now()),
            order_line_id=line.id,
        )
    )
    await session.commit()

    r = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Món bỏ",
            "source": "Món đã chế biến",
            "lines": [
                {
                    "order_line_id": line.id,
                    "servings": 2,
                }
            ],
        },
        headers=h,
    )

    assert r.status_code == 201, r.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 10
    again = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Món bỏ",
            "source": "Món đã chế biến",
            "lines": [
                {
                    "order_line_id": line.id,
                    "servings": 1,
                }
            ],
        },
        headers=h,
    )
    assert again.status_code == 422


@pytest.mark.anyio
async def test_stocktake_issue_requires_a_confirmed_session(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Hủy do kiểm kê",
            "source": "Kiểm kê",
            "lines": [{"ingredient_id": ing.id, "quantity": 1}],
        },
        headers=h,
    )
    assert r.status_code == 422


@pytest.mark.anyio
async def test_manual_issue_does_not_subtract_held_quantity_from_the_lot(session):
    """R3: the lot loses only what was drawn; held quantity stays physical."""
    from datetime import timedelta
    from decimal import Decimal
    from uuid import uuid4

    from app.modules.catalog.models import Dish, DishGroup
    from app.modules.inventory.models import IngredientLot, StockIssue, StockIssueLine
    from app.modules.inventory.stock import StockChange, apply_stock_movement
    from app.modules.sales.models import Reservation, ReservationDetail
    from app.shared import business_date

    ing = await _ingredient(session, stock_qty=10)
    _, user = await _headers(session)
    group = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Món", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        quantity_remaining=10,
        received_quantity=10,
        unit_price=1000,
        status="Còn hạn",
        received_at=business_date.now(),
    )
    session.add(lot)
    await session.flush()
    hold = Reservation(
        selection_code=uuid4().hex,
        user_id=user.id,
        dish_id=dish.id,
        quantity=9,
        expires_at=business_date.now() + timedelta(minutes=10),
        status="Đang giữ",
    )
    session.add(hold)
    await session.flush()
    session.add(ReservationDetail(reservation_id=hold.id, lot_id=lot.id, quantity=9))
    await session.commit()

    issue = StockIssue(reason="Hao hụt", status="Nháp", created_at=business_date.now())
    session.add(issue)
    await session.flush()
    issue_line = StockIssueLine(issue_id=issue.id, ingredient_id=ing.id, quantity=2)
    session.add(issue_line)
    await session.flush()
    await apply_stock_movement(
        session,
        StockChange(
            ingredient_id=ing.id,
            delta=Decimal("-2"),
            kind="Xuất thủ công",
            source_issue_line_id=issue_line.id,
        ),
    )
    await session.commit()
    await session.refresh(lot)
    await session.refresh(ing)
    await session.refresh(hold)

    assert float(lot.quantity_remaining) == 8
    assert float(ing.stock_qty) == 8
    # The hold had to be released because the write-off used its stock.
    assert hold.status == "Đã giải phóng"


async def _served_line(session, *, servings: int, recipe: list[tuple[Ingredient, int]]):
    from app.modules.catalog.models import Dish, DishGroup
    from app.modules.inventory.models import StockMovement
    from app.modules.sales.models import Order, OrderLine

    group = DishGroup(name="Nhóm món hủy", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Món hủy", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    order = Order(
        business_date=business_date.business_date_of(business_date.now()),
        table_id=None,
        order_type="Mang về",
    )
    session.add(order)
    await session.flush()
    line = OrderLine(
        order_id=order.id,
        dish_id=dish.id,
        quantity=servings,
        unit_price=50000,
        status="Đã phục vụ",
    )
    session.add(line)
    await session.flush()
    for ingredient, per_serving in recipe:
        session.add(
            StockMovement(
                ingredient_id=ingredient.id,
                kind="Trừ tự động",
                qty=-per_serving * servings,
                business_date=business_date.business_date_of(business_date.now()),
                order_line_id=line.id,
            )
        )
    await session.commit()
    return line


@pytest.mark.anyio
async def test_prepared_issue_derives_lines_and_counts_servings_once(session):
    """FR-INV-05/06: derive from the original draw, aggregate history per voucher."""
    first = await _ingredient(session, "Thịt", stock_qty=100)
    second = await _ingredient(session, "Rau", stock_qty=100)
    line = await _served_line(session, servings=3, recipe=[(first, 2), (second, 1)])
    client = await _make_client(session)
    h, _ = await _headers(session)

    preview = await client.get(
        f"/api/v1/inventory/issues/prepared-preview?order_line_id={line.id}&servings=2",
        headers=h,
    )
    assert preview.status_code == 200, preview.text
    body = preview.json()
    assert body["eligible_servings"] == 3
    assert {row["ingredient_id"]: float(row["quantity"]) for row in body["lines"]} == {
        first.id: 4.0,
        second.id: 2.0,
    }

    # Client-sent ingredient/quantity are ignored for this source.
    created = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Món bỏ",
            "source": "Món đã chế biến",
            "lines": [
                {
                    "ingredient_id": first.id,
                    "quantity": 99,
                    "order_line_id": line.id,
                    "servings": 2,
                }
            ],
        },
        headers=h,
    )
    assert created.status_code == 201, created.text
    detail = await client.get(
        f"/api/v1/inventory/issues/{created.json()['MaPhieuXuat']}", headers=h
    )
    quantities = {row["MaNguyenLieu"]: float(row["SoLuong"]) for row in detail.json()["lines"]}
    assert quantities == {first.id: 4.0, second.id: 2.0}
    assert {row["SoSuat"] for row in detail.json()["lines"]} == {2}
    await session.refresh(first)
    await session.refresh(second)
    assert float(first.stock_qty) == 100
    assert float(second.stock_qty) == 100

    # History counts 2, not 2 per ingredient, so one more serving still fits.
    remaining = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Món bỏ",
            "source": "Món đã chế biến",
            "lines": [{"order_line_id": line.id, "servings": 1}],
        },
        headers=h,
    )
    assert remaining.status_code == 201, remaining.text

    over = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Món bỏ",
            "source": "Món đã chế biến",
            "lines": [{"order_line_id": line.id, "servings": 1}],
        },
        headers=h,
    )
    assert over.status_code == 422


@pytest.mark.anyio
async def test_prepared_issue_sums_duplicate_rows_in_the_same_request(session):
    """FR-INV-06: two rows for one line in one request must not pass separately."""
    ingredient = await _ingredient(session, "Cá", stock_qty=100)
    line = await _served_line(session, servings=3, recipe=[(ingredient, 1)])
    client = await _make_client(session)
    h, _ = await _headers(session)

    response = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Món bỏ",
            "source": "Món đã chế biến",
            "lines": [
                {"order_line_id": line.id, "servings": 2},
                {"order_line_id": line.id, "servings": 2},
            ],
        },
        headers=h,
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_in_stock_lots_add_up_to_the_book_stock(session):
    """Stocktake review 19/11: only lots with something left, never a cancelled one."""
    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 5)
    await _receipt(session, client, h, ing, 5)
    cancelled = await _receipt(session, client, h, ing, 3)
    r = await client.delete(f"/api/v1/inventory/receipts/{cancelled}", headers=h)
    assert r.status_code in (200, 204), r.text
    r = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 5}]},
        headers=h,
    )
    assert r.status_code == 201, r.text

    everything = await client.get(f"/api/v1/inventory/lots?ingredient_id={ing.id}", headers=h)
    assert everything.json()["total"] == 3
    r = await client.get(f"/api/v1/inventory/lots?ingredient_id={ing.id}&in_stock=true", headers=h)
    assert r.status_code == 200, r.text
    lots = r.json()["items"]
    assert r.json()["total"] == 1
    await session.refresh(ing)
    assert sum(float(lot["SoLuongConLai"]) for lot in lots) == float(ing.stock_qty) == 5


@pytest.mark.anyio
async def test_in_stock_lots_keep_expired_and_fifo_order(session):
    from datetime import timedelta

    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    ing = await _ingredient(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    await _receipt(session, client, h, ing, 4)
    await _receipt(session, client, h, ing, 6)
    rows = (
        (
            await session.execute(
                sel(IngredientLot)
                .where(IngredientLot.ingredient_id == ing.id)
                .order_by(IngredientLot.received_at, IngredientLot.id)
            )
        )
        .scalars()
        .all()
    )
    older, newer = rows
    older.expiry_date = business_date.business_date_of(business_date.now()) - timedelta(days=2)
    await session.commit()

    r = await client.get(f"/api/v1/inventory/lots?ingredient_id={ing.id}&in_stock=true", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 2
    assert [lot["MaLoNguyenLieu"] for lot in body["items"]] == [older.id, newer.id]
    assert body["items"][0]["TrangThai"] == "Hết hạn"


# --- Proposed expiry write-off awaiting approval (BA review 19/11, việc 2) ---

PROPOSAL_NOTE = "Hệ thống đề xuất hủy các lô đã quá hạn sử dụng."


async def _expired_lot(session, client, headers, ing, qty, days_ago=2):
    """Receive `qty`, then age that receipt's lot past its expiry; returns the lot."""
    from datetime import timedelta

    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot

    await _receipt(session, client, headers, ing, qty)
    lot = (
        await session.execute(
            sel(IngredientLot)
            .where(IngredientLot.ingredient_id == ing.id)
            .order_by(IngredientLot.id.desc())
            .limit(1)
        )
    ).scalar_one()
    lot.expiry_date = business_date.business_date_of(business_date.now()) - timedelta(days=days_ago)
    await session.commit()
    return lot


async def _propose(client, headers):
    r = await client.post("/api/v1/inventory/issues/propose-expired", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["MaPhieuXuat"]


async def _roles(session):
    kitchen, kitchen_user = await _headers(session, "WAREHOUSE", "kho02")
    manager, manager_user = await _headers(session, "MANAGER", "ql02")
    cashier, _ = await _headers(session, "CASHIER", "thungan02")
    return kitchen, kitchen_user, manager, manager_user, cashier


@pytest.mark.anyio
async def test_proposal_creates_pending_voucher_without_moving_stock(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssue, StockIssueLine

    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    lot = await _expired_lot(session, client, kitchen, ing, 4)

    issue_id = await _propose(client, kitchen)

    assert issue_id is not None
    issue = await session.get(StockIssue, issue_id)
    assert (issue.reason, issue.source, issue.status) == ("Hết hạn", "Nguyên liệu", "Chờ duyệt")
    assert issue.created_by is None
    assert issue.issue_date is None
    assert issue.note == PROPOSAL_NOTE
    lines = (
        (await session.execute(sel(StockIssueLine).where(StockIssueLine.issue_id == issue_id)))
        .scalars()
        .all()
    )
    assert [(ln.ingredient_id, ln.lot_id, float(ln.quantity)) for ln in lines] == [
        (ing.id, lot.id, 4.0)
    ]
    await session.refresh(ing)
    assert float(ing.stock_qty) == 4
    assert await lot_total(session, ing.id) == 4
    assert [m["LoaiGiaoDich"] for m in await movements_for(session, ing.id)] == ["Nhập"]


@pytest.mark.anyio
async def test_proposal_is_idempotent(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)

    assert await _propose(client, kitchen) is not None
    assert await _propose(client, kitchen) is None
    listing = await client.get("/api/v1/inventory/issues?status=Chờ duyệt", headers=kitchen)
    assert listing.json()["total"] == 1


@pytest.mark.anyio
async def test_lot_expiring_today_is_not_proposed(session):
    from datetime import timedelta

    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    lot = await _expired_lot(session, client, kitchen, ing, 4, days_ago=0)
    assert lot.expiry_date == business_date.business_date_of(business_date.now())

    assert await _propose(client, kitchen) is None

    lot.expiry_date -= timedelta(days=1)
    await session.commit()
    assert await _propose(client, kitchen) is not None


@pytest.mark.anyio
async def test_kitchen_approval_draws_the_exact_lot(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import IngredientLot, StockIssue, StockIssueLine

    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, kitchen_user, *_ = await _roles(session)
    await _receipt(session, client, kitchen, ing, 6)  # a fresh lot that must stay untouched
    expired_id = (await _expired_lot(session, client, kitchen, ing, 4)).id
    kitchen_id, ing_id = kitchen_user.id, ing.id
    issue_id = await _propose(client, kitchen)

    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=kitchen)

    assert r.status_code == 200, r.text
    assert r.json() == {"MaPhieuXuat": issue_id, "TrangThai": "Đã xác nhận"}
    session.expire_all()
    issue = await session.get(StockIssue, issue_id)
    assert issue.status == "Đã xác nhận"
    assert issue.approved_by == kitchen_id
    assert issue.approved_at is not None
    assert issue.issue_date == issue.approved_at
    line = (
        await session.execute(sel(StockIssueLine).where(StockIssueLine.issue_id == issue_id))
    ).scalar_one()
    assert line.estimated_cost == 4000
    lots = {
        lot.id: float(lot.quantity_remaining)
        for lot in (
            await session.execute(sel(IngredientLot).where(IngredientLot.ingredient_id == ing_id))
        ).scalars()
    }
    assert lots[expired_id] == 0
    assert sorted(lots.values()) == [0, 6]
    await session.refresh(ing)
    assert float(ing.stock_qty) == 6
    drawn = [
        m for m in await movements_for(session, ing_id) if m["LoaiGiaoDich"] == "Xuất thủ công"
    ]
    assert len(drawn) == 1
    assert drawn[0]["MaChiTietXuat"] == line.id
    assert drawn[0]["MaLoNguyenLieu"] == expired_id


@pytest.mark.anyio
async def test_manager_can_approve(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, _, manager, manager_user, _ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, manager)

    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=manager)

    assert r.status_code == 200, r.text
    detail = (await client.get(f"/api/v1/inventory/issues/{issue_id}", headers=manager)).json()
    assert detail["NguoiDuyet"] == manager_user.id
    assert detail["TenNguoiDuyet"] == manager_user.full_name


@pytest.mark.anyio
async def test_cashier_cannot_approve_or_reject(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, _, _, _, cashier = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, kitchen)

    for action in ("approve", "reject"):
        r = await client.post(f"/api/v1/inventory/issues/{issue_id}/{action}", headers=cashier)
        assert r.status_code == 403, (action, r.text)
    propose = await client.post("/api/v1/inventory/issues/propose-expired", headers=cashier)
    assert propose.status_code == 403
    detail = (await client.get(f"/api/v1/inventory/issues/{issue_id}", headers=kitchen)).json()
    assert detail["TrangThai"] == "Chờ duyệt"


@pytest.mark.anyio
async def test_reject_keeps_stock_and_lot_is_never_proposed_again(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, kitchen_user, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, kitchen)

    r = await client.post(
        f"/api/v1/inventory/issues/{issue_id}/reject",
        json={"note": "Còn dùng được"},
        headers=kitchen,
    )

    assert r.status_code == 200, r.text
    assert r.json() == {"MaPhieuXuat": issue_id, "TrangThai": "Đã từ chối"}
    detail = (await client.get(f"/api/v1/inventory/issues/{issue_id}", headers=kitchen)).json()
    assert detail["NguoiDuyet"] == kitchen_user.id
    assert detail["NgayDuyet"] is not None
    assert detail["GhiChu"] == f"{PROPOSAL_NOTE} Lý do từ chối: Còn dùng được"
    await session.refresh(ing)
    assert float(ing.stock_qty) == 4
    assert await lot_total(session, ing.id) == 4
    assert await _propose(client, kitchen) is None


@pytest.mark.anyio
async def test_reject_without_a_body_is_allowed(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, kitchen)

    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/reject", headers=kitchen)

    assert r.status_code == 200, r.text
    detail = (await client.get(f"/api/v1/inventory/issues/{issue_id}", headers=kitchen)).json()
    assert detail["GhiChu"] == PROPOSAL_NOTE


@pytest.mark.anyio
async def test_approve_or_reject_twice_is_a_business_error(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)
    approved = await _propose(client, kitchen)
    ok = await client.post(f"/api/v1/inventory/issues/{approved}/approve", headers=kitchen)
    assert ok.status_code == 200, ok.text
    await _expired_lot(session, client, kitchen, ing, 3)
    rejected = await _propose(client, kitchen)
    ok = await client.post(f"/api/v1/inventory/issues/{rejected}/reject", headers=kitchen)
    assert ok.status_code == 200, ok.text

    for issue_id in (approved, rejected):
        for action in ("approve", "reject"):
            r = await client.post(f"/api/v1/inventory/issues/{issue_id}/{action}", headers=kitchen)
            assert r.status_code == 422, (issue_id, action, r.text)
            assert "Chỉ duyệt hoặc từ chối phiếu đang chờ duyệt." in r.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 3  # only the first proposal was posted


@pytest.mark.anyio
async def test_open_stocktake_blocks_proposal_and_approval(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, kitchen)
    await _expired_lot(session, client, kitchen, ing, 2)
    stocktake = await client.post("/api/v1/inventory/stocktakes", headers=kitchen)
    assert stocktake.status_code == 201, stocktake.text

    assert await _propose(client, kitchen) is None
    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=kitchen)
    assert r.status_code == 422, r.text
    await session.refresh(ing)
    assert float(ing.stock_qty) == 6


@pytest.mark.anyio
async def test_approval_draws_only_what_is_left(session):
    from sqlalchemy import select as sel

    from app.modules.inventory.models import StockIssueLine

    ing = await _ingredient(session)
    other_ing = await _ingredient(session, "Cá")
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    lot_id = (await _expired_lot(session, client, kitchen, ing, 5)).id
    other_id = (await _expired_lot(session, client, kitchen, other_ing, 2)).id
    ing_id = ing.id
    issue_id = await _propose(client, kitchen)
    # 3 of the lot are written off by hand after the proposal was made.
    r = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Hết hạn",
            "lines": [{"ingredient_id": ing_id, "quantity": 3, "lot_id": lot_id}],
        },
        headers=kitchen,
    )
    assert r.status_code == 201, r.text

    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=kitchen)

    assert r.status_code == 200, r.text
    session.expire_all()
    lines = (
        (await session.execute(sel(StockIssueLine).where(StockIssueLine.issue_id == issue_id)))
        .scalars()
        .all()
    )
    assert sorted((ln.lot_id, float(ln.quantity)) for ln in lines) == sorted(
        [(lot_id, 2.0), (other_id, 2.0)]
    )
    await session.refresh(ing)
    assert float(ing.stock_qty) == 0


@pytest.mark.anyio
async def test_approval_with_nothing_left_errors(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    lot = await _expired_lot(session, client, kitchen, ing, 5)
    issue_id = await _propose(client, kitchen)
    r = await client.post(
        "/api/v1/inventory/issues",
        json={
            "reason": "Hết hạn",
            "lines": [{"ingredient_id": ing.id, "quantity": 5, "lot_id": lot.id}],
        },
        headers=kitchen,
    )
    assert r.status_code == 201, r.text

    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=kitchen)

    assert r.status_code == 422, r.text
    assert "Các lô trong phiếu không còn hàng; hãy từ chối phiếu này." in r.text
    detail = (await client.get(f"/api/v1/inventory/issues/{issue_id}", headers=kitchen)).json()
    assert detail["TrangThai"] == "Chờ duyệt"
    reject = await client.post(f"/api/v1/inventory/issues/{issue_id}/reject", headers=kitchen)
    assert reject.status_code == 200, reject.text


@pytest.mark.anyio
async def test_waste_cost_ignores_pending_and_rejected_vouchers(session):
    from app.modules.reports.queries import waste_cost

    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    today = business_date.business_date_of(business_date.now())
    month = today.year * 100 + today.month
    await _expired_lot(session, client, kitchen, ing, 4)
    rejected = await _propose(client, kitchen)
    await client.post(f"/api/v1/inventory/issues/{rejected}/reject", headers=kitchen)
    await _expired_lot(session, client, kitchen, ing, 3)
    pending = await _propose(client, kitchen)
    assert pending is not None
    assert await waste_cost(session, month) == (0, 0)

    r = await client.post(f"/api/v1/inventory/issues/{pending}/approve", headers=kitchen)
    assert r.status_code == 200, r.text

    waste, unvalued = await waste_cost(session, month)
    assert (float(waste), unvalued) == (3000.0, 0)


@pytest.mark.anyio
async def test_list_issues_filters_by_status(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, kitchen_user, *_ = await _roles(session)
    await _receipt(session, client, kitchen, ing, 9)
    manual = await client.post(
        "/api/v1/inventory/issues",
        json={"reason": "Hao hụt", "lines": [{"ingredient_id": ing.id, "quantity": 1}]},
        headers=kitchen,
    )
    assert manual.status_code == 201, manual.text
    await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, kitchen)

    async def listed(status):
        r = await client.get(f"/api/v1/inventory/issues?status={status}", headers=kitchen)
        assert r.status_code == 200, r.text
        return r.json()

    pending = await listed("Chờ duyệt")
    confirmed = await listed("Đã xác nhận")
    assert [row["MaPhieuXuat"] for row in pending["items"]] == [issue_id]
    assert pending["items"][0]["NguoiLap"] is None
    assert pending["items"][0]["NguoiDuyet"] is None
    assert [row["MaPhieuXuat"] for row in confirmed["items"]] == [manual.json()["MaPhieuXuat"]]
    everything = await client.get("/api/v1/inventory/issues", headers=kitchen)
    assert everything.json()["total"] == 2

    await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=kitchen)
    row = next(r for r in (await listed("Đã xác nhận"))["items"] if r["MaPhieuXuat"] == issue_id)
    assert row["NguoiDuyet"] == kitchen_user.id
    assert row["NgayDuyet"] is not None


@pytest.mark.anyio
async def test_proposed_issue_detail_shows_lot_and_expiry(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    lot = await _expired_lot(session, client, kitchen, ing, 4)
    issue_id = await _propose(client, kitchen)

    detail = (await client.get(f"/api/v1/inventory/issues/{issue_id}", headers=kitchen)).json()

    assert detail["NguoiLap"] is None
    assert detail["TenNguoiDuyet"] is None
    assert detail["NgayDuyet"] is None
    [line] = detail["lines"]
    assert line["MaLoNguyenLieu"] == lot.id
    assert line["HanSuDung"] == lot.expiry_date.isoformat()


@pytest.mark.anyio
async def test_pending_proposal_lot_still_listed_for_stocktake(session):
    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    lot = await _expired_lot(session, client, kitchen, ing, 4)
    assert await _propose(client, kitchen) is not None

    r = await client.get(
        f"/api/v1/inventory/lots?ingredient_id={ing.id}&in_stock=true", headers=kitchen
    )

    assert r.status_code == 200, r.text
    assert [item["MaLoNguyenLieu"] for item in r.json()["items"]] == [lot.id]


@pytest.mark.anyio
async def test_tick_proposes_once_and_survives_a_proposal_failure(
    session, session_factory, monkeypatch
):
    from sqlalchemy import func
    from sqlalchemy import select as sel

    from app.modules.inventory import lot_status, service
    from app.modules.inventory.models import StockIssue

    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 4)

    async def boom(_session):
        raise RuntimeError("proposal failed")

    with monkeypatch.context() as patched:
        patched.setattr(service, "propose_expiry_write_off", boom)
        await lot_status.lot_status_tick(factory=session_factory)  # must not raise

    await lot_status.lot_status_tick(factory=session_factory)
    await lot_status.lot_status_tick(factory=session_factory)  # idempotent
    session.expire_all()
    count = (await session.execute(sel(func.count()).select_from(StockIssue))).scalar_one()
    assert count == 1


@pytest.mark.anyio
async def test_waste_counts_in_the_month_the_proposal_was_approved(session, monkeypatch):
    from datetime import timedelta

    from app.modules.reports.queries import waste_cost
    from tests.helpers import FIXED_NOW

    ing = await _ingredient(session)
    client = await _make_client(session)
    kitchen, *_ = await _roles(session)
    await _expired_lot(session, client, kitchen, ing, 3)
    issue_id = await _propose(client, kitchen)
    proposed = business_date.business_date_of(business_date.now())
    later = FIXED_NOW + timedelta(days=40)
    approved = business_date.business_date_of(later)
    assert (approved.year, approved.month) != (proposed.year, proposed.month)

    monkeypatch.setattr(business_date, "now", lambda: later)
    r = await client.post(f"/api/v1/inventory/issues/{issue_id}/approve", headers=kitchen)
    assert r.status_code == 200, r.text

    first, _ = await waste_cost(session, proposed.year * 100 + proposed.month)
    second, _ = await waste_cost(session, approved.year * 100 + approved.month)
    assert (float(first), float(second)) == (0.0, 3000.0)


@pytest.mark.anyio
async def test_proposal_takes_the_stock_operations_lock(session, monkeypatch):
    from app.modules.inventory import service

    calls = []
    real = service.lock_stock_operations

    async def spy(s):
        calls.append(1)
        await real(s)

    monkeypatch.setattr(service, "lock_stock_operations", spy)
    assert await service.propose_expiry_write_off(session) is None
    assert calls == [1]
