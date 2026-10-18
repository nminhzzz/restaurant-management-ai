"""FR-SALE-19/23/35: verification, reopen and closing an order without money."""

import pytest
from sqlalchemy import func, select

from app.modules.catalog.models import (
    DiningTable,
    Dish,
    DishGroup,
    DishPriceVersion,
    Ingredient,
    Recipe,
    RecipeItem,
)
from app.modules.inventory.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    IngredientLot,
    MonthlyAverageCost,
)
from app.modules.sales.models import Invoice, PaymentTransaction
from app.modules.sales.payments import PAYMENT_CLOSED_UNPAID
from app.shared import business_date
from app.shared.enums import VersionStatus


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _setup(session):
    group = DishGroup(name="Nhóm ngoại lệ", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Món ngoại lệ", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    ingredient = Ingredient(
        name="NL ngoại lệ", unit="kg", min_stock=1, stock_qty=5, is_deleted=False
    )
    session.add(ingredient)
    await session.flush()
    bd = business_date.business_date_of(business_date.now())
    session.add(
        MonthlyAverageCost(
            ingredient_id=ingredient.id,
            month=bd.year * 100 + bd.month,
            avg_cost=1000,
            total_qty=1,
        )
    )
    session.add_all(
        [
            DishPriceVersion(
                dish_id=dish.id,
                price=50000,
                business_date=bd,
                status=VersionStatus.HIEU_LUC.value,
                change_type="Tạo mới",
            ),
            Recipe(
                dish_id=dish.id,
                business_date=bd,
                status=VersionStatus.HIEU_LUC.value,
                change_type="Tạo mới",
            ),
        ]
    )
    await session.flush()
    recipe = await session.scalar(select(Recipe).where(Recipe.dish_id == dish.id))
    assert recipe is not None
    session.add(RecipeItem(recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=1))
    receipt = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=business_date.now())
    session.add(receipt)
    await session.flush()
    line = GoodsReceiptLine(
        receipt_id=receipt.id, ingredient_id=ingredient.id, quantity=5, unit_price=1000
    )
    session.add(line)
    await session.flush()
    session.add(
        IngredientLot(
            ingredient_id=ingredient.id,
            receipt_line_id=line.id,
            quantity_remaining=5,
            status="Còn hạn",
            received_at=business_date.now(),
        )
    )
    table = DiningTable(name="Bàn ngoại lệ", is_deleted=False, status="Trống")
    session.add(table)
    await session.flush()
    await session.commit()
    return dish, table


async def _open_order(api_client, cashier_token, dish, table):
    created = await api_client.post(
        "/api/v1/sales/orders",
        json={"MaBan": table.id, "lines": [{"MaMon": dish.id, "SoLuong": 1}]},
        headers=_auth(cashier_token),
    )
    assert created.status_code == 201, created.text
    order_id = created.json()["MaOrder"]
    qr = await api_client.post(
        f"/api/v1/sales/orders/{order_id}/pay/qr", headers=_auth(cashier_token)
    )
    assert qr.status_code == 201, qr.text
    return order_id, qr.json()["MaGiaoDich"]


@pytest.mark.anyio
async def test_requesting_verification_locks_the_order(
    api_client, session, manager_token, cashier_token
):
    dish, table = await _setup(session)
    order_id, payment_id = await _open_order(api_client, cashier_token, dish, table)

    response = await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/request-verification",
        headers=_auth(cashier_token),
    )

    assert response.status_code == 200
    assert response.json()["TrangThai"] == "Chờ xác minh thanh toán"
    order = (
        await api_client.get(f"/api/v1/sales/orders/{order_id}", headers=_auth(manager_token))
    ).json()
    assert order["TrangThai"] == "Chờ xác minh thanh toán"
    blocked = await api_client.post(
        f"/api/v1/sales/orders/{order_id}/lines",
        json={"MaMon": dish.id, "SoLuong": 1},
        headers=_auth(cashier_token),
    )
    assert blocked.status_code == 422


@pytest.mark.anyio
async def test_manager_reopens_a_verifying_order_for_another_payment(
    api_client, session, manager_token, cashier_token
):
    dish, table = await _setup(session)
    order_id, payment_id = await _open_order(api_client, cashier_token, dish, table)
    await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/request-verification",
        headers=_auth(cashier_token),
    )

    forbidden = await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/reopen",
        json={"reason": "khách chuyển nhầm"},
        headers=_auth(cashier_token),
    )
    reopened = await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/reopen",
        json={"reason": "khách chuyển nhầm"},
        headers=_auth(manager_token),
    )

    assert forbidden.status_code == 403
    assert reopened.status_code == 200
    assert reopened.json()["TrangThai"] == "Đang mở"
    payment = await session.get(PaymentTransaction, payment_id)
    assert payment is not None and payment.status == "Đã hủy"
    retry = await api_client.post(
        f"/api/v1/sales/orders/{order_id}/pay/qr", headers=_auth(cashier_token)
    )
    assert retry.status_code == 201


@pytest.mark.anyio
async def test_closing_unpaid_sets_a_terminal_status_without_an_invoice(
    api_client, session, manager_token, cashier_token
):
    dish, table = await _setup(session)
    order_id, payment_id = await _open_order(api_client, cashier_token, dish, table)
    await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/request-verification",
        headers=_auth(cashier_token),
    )

    closed = await api_client.post(
        f"/api/v1/sales/orders/{order_id}/close-unpaid",
        json={"reason": "không nhận được tiền"},
        headers=_auth(manager_token),
    )

    assert closed.status_code == 200
    assert closed.json()["TrangThai"] == PAYMENT_CLOSED_UNPAID
    payment = await session.get(PaymentTransaction, payment_id)
    assert payment is not None and payment.status == PAYMENT_CLOSED_UNPAID
    assert (
        await session.scalar(
            select(func.count()).select_from(Invoice).where(Invoice.order_id == order_id)
        )
        == 0
    )
    report = await api_client.get(
        "/api/v1/reports/closed-unpaid",
        params={"month": business_date.now().strftime("%Y-%m")},
        headers=_auth(manager_token),
    )
    assert report.status_code == 200
    assert report.json()["SoLuong"] == 1
    assert float(report.json()["TongGiaTri"]) == 50000
    assert float(report.json()["TongGiaVon"]) == 1000
    assert float(report.json()["items"][0]["GiaVon"]) == 1000
    assert report.json()["items"][0]["LyDo"] == "không nhận được tiền"
    retry = await api_client.post(
        f"/api/v1/sales/orders/{order_id}/pay/cash", headers=_auth(cashier_token)
    )
    assert retry.status_code == 422


@pytest.mark.anyio
async def test_verifying_money_is_provisional_and_appears_in_pending_list(
    api_client, session, manager_token, cashier_token
):
    dish, table = await _setup(session)
    _, payment_id = await _open_order(api_client, cashier_token, dish, table)
    await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/request-verification",
        headers=_auth(cashier_token),
    )
    month = business_date.now().strftime("%Y-%m")

    revenue = await api_client.get(
        "/api/v1/reports/revenue", params={"month": month}, headers=_auth(manager_token)
    )
    pending = await api_client.get(
        "/api/v1/reports/pending-payments",
        params={"month": month},
        headers=_auth(manager_token),
    )

    assert revenue.status_code == 200
    assert float(revenue.json()["provisional"]) == 50000
    assert float(revenue.json()["total"]) == 50000
    assert pending.status_code == 200
    assert any(
        row["MaGiaoDich"] == payment_id and row["TrangThai"] == "Chờ xác minh thanh toán"
        for row in pending.json()["items"]
    )


@pytest.mark.anyio
async def test_manager_can_confirm_a_verifying_payment(
    api_client, session, manager_token, cashier_token
):
    dish, table = await _setup(session)
    order_id, payment_id = await _open_order(api_client, cashier_token, dish, table)
    await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/request-verification",
        headers=_auth(cashier_token),
    )

    resolved = await api_client.post(
        f"/api/v1/sales/payments/{payment_id}/resolve",
        json={"outcome": "received"},
        headers=_auth(manager_token),
    )

    assert resolved.status_code == 200
    payment = await session.get(PaymentTransaction, payment_id)
    assert payment is not None and payment.status == "Thành công"
    order = (
        await api_client.get(f"/api/v1/sales/orders/{order_id}", headers=_auth(manager_token))
    ).json()
    assert order["TrangThai"] == "Đã thanh toán"
    assert (
        await session.scalar(
            select(func.count()).select_from(Invoice).where(Invoice.order_id == order_id)
        )
        == 1
    )
