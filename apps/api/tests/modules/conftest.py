"""Fixtures for settings and catalog modules."""

import time
from datetime import date, datetime
from decimal import Decimal
from itertools import count
from types import SimpleNamespace

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.database import get_session
from app.core.security import hash_password
from app.main import app
from app.modules.catalog.models import Dish, DishGroup
from app.modules.settings.models import User
from app.modules.settings.service import seed_reference_data


@pytest_asyncio.fixture
async def active_user(session):
    await seed_reference_data(session)
    user = User(
        username="thungan01",
        password_hash=hash_password("mat-khau-dung"),
        full_name="Thu Ngan 01",
        role_id="CASHIER",
        status="Hoạt động",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


@pytest_asyncio.fixture
async def locked_user(session):
    await seed_reference_data(session)
    user = User(
        username="thungan01",
        password_hash=hash_password("mat-khau-dung"),
        full_name="Thu Ngan 01",
        role_id="CASHIER",
        status="Đã khóa",
    )
    session.add(user)
    await session.flush()
    await session.commit()
    return user


# Catalog fixtures
@pytest_asyncio.fixture
async def group(session):
    await seed_reference_data(session)
    g = DishGroup(name="Món chính", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    await session.commit()
    return g


@pytest_asyncio.fixture
async def other_group(session):
    await seed_reference_data(session)
    g = DishGroup(name="Khai vị", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    await session.commit()
    return g


@pytest_asyncio.fixture
async def three_groups(session):
    await seed_reference_data(session)
    groups = []
    for i, name in enumerate(["Món chính", "Khai vị", "Tráng miệng"], start=1):
        g = DishGroup(name=name, display_order=i, is_deleted=False)
        session.add(g)
        await session.flush()
        groups.append(g)
    await session.commit()
    return groups


@pytest_asyncio.fixture
async def dish(session, group):
    d = Dish(
        name="Phở bò",
        group_id=group.id,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    await session.commit()
    return d


@pytest_asyncio.fixture
async def draft_dish(session, group):
    d = Dish(
        name="Món nháp",
        group_id=group.id,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    await session.commit()
    return d


@pytest_asyncio.fixture
async def three_dishes(session, group):
    dishes = []
    for name in ["Phở bò", "Bún chả", "Cơm tấm"]:
        d = Dish(
            name=name,
            group_id=group.id,
            hide_manual=False,
            out_of_stock_manual=False,
            out_of_stock_auto=False,
            is_deleted=False,
        )
        session.add(d)
        await session.flush()
        dishes.append(d)
    await session.commit()
    return dishes


@pytest_asyncio.fixture
async def group_with_dish(session):
    await seed_reference_data(session)
    g = DishGroup(name="Nhóm có món", display_order=1, is_deleted=False)
    session.add(g)
    await session.flush()
    d = Dish(
        name="Món trong nhóm",
        group_id=g.id,
        hide_manual=False,
        out_of_stock_manual=False,
        out_of_stock_auto=False,
        is_deleted=False,
    )
    session.add(d)
    await session.flush()
    await session.commit()
    # attach helper attrs
    g.dish_id = d.id
    return g


@pytest_asyncio.fixture
async def dish_with_pending_price(session, dish):
    from app.modules.catalog.models import DishPriceVersion
    from tests.helpers import tomorrow

    v = DishPriceVersion(
        dish_id=dish.id, price=50000, business_date=tomorrow(), status="Nháp", change_type="Tạo mới"
    )
    session.add(v)
    await session.flush()
    await session.commit()
    return dish


@pytest_asyncio.fixture
async def free_table(session):
    from app.modules.catalog.models import DiningTable

    await seed_reference_data(session)
    t = DiningTable(name="Bàn 1", is_deleted=False)
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def occupied_table(session):
    from app.modules.catalog.models import DiningTable

    await seed_reference_data(session)
    t = DiningTable(name="Bàn 2", is_deleted=False)
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def fresh_ingredient(session):
    from app.modules.catalog.models import Ingredient

    await seed_reference_data(session)
    ing = Ingredient(
        name="Bột mì", unit="kg", min_stock=5, stock_qty=0, is_deleted=False, unit_locked=False
    )
    session.add(ing)
    await session.flush()
    await session.commit()
    return ing


@pytest_asyncio.fixture
async def three_ingredients(session):
    from app.modules.catalog.models import Ingredient

    await seed_reference_data(session)
    ings = []
    for name in ["Hành lá", "Bột mì", "Cà chua"]:
        ing = Ingredient(
            name=name, unit="kg", min_stock=5, stock_qty=0, is_deleted=False, unit_locked=False
        )
        session.add(ing)
        await session.flush()
        ings.append(ing)
    await session.commit()
    return ings


@pytest_asyncio.fixture
async def ingredient_in_recipe(session, dish, fresh_ingredient):
    from app.modules.catalog.models import Recipe, RecipeItem
    from app.shared import business_date
    from app.shared.enums import VersionStatus

    r = Recipe(
        dish_id=dish.id,
        business_date=business_date.business_date_of(business_date.now()),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
        effective_from=business_date.now(),
    )
    session.add(r)
    await session.flush()
    session.add(RecipeItem(recipe_id=r.id, ingredient_id=fresh_ingredient.id, quantity=0.2))
    fresh_ingredient.unit_locked = True
    await session.flush()
    await session.commit()
    return fresh_ingredient


@pytest_asyncio.fixture
async def fresh_supplier(session):
    from app.modules.catalog.models import Supplier

    await seed_reference_data(session)
    s = Supplier(name="NCC A", is_deleted=False)
    session.add(s)
    await session.flush()
    await session.commit()
    return s


@pytest_asyncio.fixture
async def supplier_with_receipts(session, fresh_supplier):

    from app.modules.inventory.models import GoodsReceipt

    for _ in range(2):
        gr = GoodsReceipt(supplier_id=fresh_supplier.id, status="Đã nhập")
        session.add(gr)
        await session.flush()
    await session.commit()
    return fresh_supplier


@pytest_asyncio.fixture
async def config_with_default_threshold(session):
    await seed_reference_data(session)
    from sqlalchemy import select

    from app.modules.settings.models import SystemConfig

    cfg = (await session.execute(select(SystemConfig))).scalar_one()
    cfg.default_stock_threshold = 7
    await session.flush()
    await session.commit()
    return cfg


@pytest_asyncio.fixture
async def dish_with_recipe(session, dish, fresh_ingredient):
    from app.modules.catalog.models import Recipe, RecipeItem
    from app.shared import business_date
    from app.shared.enums import VersionStatus

    r = Recipe(
        dish_id=dish.id,
        business_date=business_date.business_date_of(business_date.now()),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
        effective_from=business_date.now(),
    )
    session.add(r)
    await session.flush()
    session.add(RecipeItem(recipe_id=r.id, ingredient_id=fresh_ingredient.id, quantity=0.2))
    fresh_ingredient.unit_locked = True
    await session.flush()
    await session.commit()
    return dish


@pytest_asyncio.fixture
async def flour(session, fresh_ingredient):
    return fresh_ingredient


# --- Phase 4 fixtures ---
@pytest_asyncio.fixture
async def table(session):
    from app.modules.catalog.models import DiningTable

    t = DiningTable(name="Bàn A", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def table2(session):
    from app.modules.catalog.models import DiningTable

    t = DiningTable(name="Bàn B", is_deleted=False, status="Trống")
    session.add(t)
    await session.flush()
    await session.commit()
    return t


@pytest_asyncio.fixture
async def scarce_dish(session, group):
    """Dish with tiny stock (1 unit) so ordering 99 fails."""
    from app.modules.catalog.models import Dish, DishPriceVersion, Ingredient, Recipe, RecipeItem
    from app.modules.inventory.models import GoodsReceipt, GoodsReceiptLine, IngredientLot
    from app.shared import business_date as _bd
    from app.shared.enums import VersionStatus

    dish = Dish(name="Món hiếm", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    ing = Ingredient(name="NL hiếm", unit="kg", min_stock=1, stock_qty=1, is_deleted=False)
    session.add(ing)
    await session.flush()
    pv = DishPriceVersion(
        dish_id=dish.id,
        price=10000,
        business_date=_bd.business_date_of(_bd.now()),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    session.add(pv)
    await session.flush()
    r = Recipe(
        dish_id=dish.id,
        business_date=_bd.business_date_of(_bd.now()),
        status=VersionStatus.HIEU_LUC.value,
        change_type="Tạo mới",
    )
    session.add(r)
    await session.flush()
    session.add(RecipeItem(recipe_id=r.id, ingredient_id=ing.id, quantity=1))
    # lot with 1 remaining
    gr = GoodsReceipt(supplier_id=None, status="Nháp", receipt_date=_bd.now())
    session.add(gr)
    await session.flush()
    gl = GoodsReceiptLine(receipt_id=gr.id, ingredient_id=ing.id, quantity=1, unit_price=5000)
    session.add(gl)
    await session.flush()
    lot = IngredientLot(
        ingredient_id=ing.id,
        receipt_line_id=gl.id,
        quantity_remaining=1,
        status="Còn hạn",
        received_at=_bd.now(),
    )
    session.add(lot)
    await session.flush()
    await session.commit()
    return dish


# --- Phase 5 report fixtures (contract in docs/plans/phases/phase-5-reports.md) ---

_ORDER_CODE = count(1000)


def _sep(day: int) -> date:
    return date(2026, 9, day)


def _aug(day: int) -> date:
    return date(2026, 8, day)


@pytest_asyncio.fixture
async def api_client(session):
    """An HTTP client whose requests run against the test session."""

    async def _get_session():
        yield session

    app.dependency_overrides[get_session] = _get_session
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def _r_table(session, name="Bàn R"):
    from app.modules.catalog.models import DiningTable

    table = DiningTable(name=name, status="Trống", is_deleted=False)
    session.add(table)
    await session.flush()
    return table


async def _r_dish(session, name):
    group = DishGroup(name="Nhóm báo cáo", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name=name, group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    return dish


async def _r_order(
    session, *, bd, status="Đang mở", table_id=None, order_type="Tại chỗ", at=None, reason=None
):
    from app.modules.sales.models import Order

    order = Order(
        business_date=bd,
        created_at=at or datetime(bd.year, bd.month, bd.day, 12, 0),
        status=status,
        table_id=table_id,
        order_type=order_type,
        display_code=f"ORD-R{next(_ORDER_CODE)}",
        cancel_reason=reason,
    )
    session.add(order)
    await session.flush()
    return order


async def _r_line(session, order, dish, quantity, unit_price, *, status="Chờ", recipe_id=None):
    from app.modules.sales.models import OrderLine

    line = OrderLine(
        order_id=order.id,
        dish_id=dish.id,
        quantity=quantity,
        unit_price=Decimal(str(unit_price)),
        status=status,
        recipe_id=recipe_id,
    )
    session.add(line)
    await session.flush()
    return line


async def _r_invoice(session, order, *, bd, total):
    from app.modules.sales.models import Invoice

    invoice = Invoice(order_id=order.id, business_date=bd, total=Decimal(str(total)), print_count=1)
    session.add(invoice)
    await session.flush()
    return invoice


async def _r_payment(session, order, *, method, status, amount, bd):
    from app.modules.sales.models import PaymentTransaction

    payment = PaymentTransaction(
        order_id=order.id,
        method=method,
        status=status,
        amount=Decimal(str(amount)),
        business_date=bd,
        created_at=datetime(bd.year, bd.month, bd.day, 12, 0),
    )
    session.add(payment)
    await session.flush()
    return payment


async def _r_ingredient(session, name, avg_cost, *, month=202609):
    from app.modules.catalog.models import Ingredient
    from app.modules.inventory.models import MonthlyAverageCost

    ingredient = Ingredient(
        name=name,
        unit="kg",
        min_stock=Decimal("0"),
        stock_qty=Decimal("100"),
        is_deleted=False,
    )
    session.add(ingredient)
    await session.flush()
    session.add(
        MonthlyAverageCost(
            ingredient_id=ingredient.id,
            month=month,
            avg_cost=Decimal(str(avg_cost)),
            total_qty=Decimal("1"),
        )
    )
    await session.flush()
    return ingredient


async def _r_recipe(session, dish, ingredient, quantity, bd):
    from app.modules.catalog.models import Recipe, RecipeItem

    recipe = Recipe(dish_id=dish.id, business_date=bd, status="Hiệu lực", change_type="Tạo mới")
    session.add(recipe)
    await session.flush()
    session.add(
        RecipeItem(
            recipe_id=recipe.id, ingredient_id=ingredient.id, quantity=Decimal(str(quantity))
        )
    )
    await session.flush()
    return recipe


async def _r_issue(session, *, bd, ingredient, quantity, cost):
    from app.modules.inventory.models import StockIssue, StockIssueLine

    issue = StockIssue(
        reason="Hao hụt",
        status="Đã duyệt",
        created_at=datetime(bd.year, bd.month, bd.day, 12, 0),
    )
    session.add(issue)
    await session.flush()
    line = StockIssueLine(
        issue_id=issue.id,
        ingredient_id=ingredient.id,
        quantity=Decimal(str(quantity)),
        estimated_cost=Decimal(str(cost)),
    )
    session.add(line)
    await session.flush()
    return line


@pytest_asyncio.fixture
async def invoices_in_september(session):
    """Two settled invoices on two tables, one per payment method."""
    table_a = await _r_table(session, "Bàn Sep 1")
    table_b = await _r_table(session, "Bàn Sep 2")
    dish = await _r_dish(session, "Món hóa đơn")
    total = Decimal(0)
    for table, method, quantity, price in (
        (table_a, "Tiền mặt", 2, 50000),
        (table_b, "QR", 3, 40000),
    ):
        order = await _r_order(session, bd=_sep(10), table_id=table.id)
        await _r_line(session, order, dish, quantity, price)
        amount = Decimal(quantity) * Decimal(price)
        await _r_invoice(session, order, bd=_sep(10), total=amount)
        await _r_payment(
            session, order, method=method, status="Thành công", amount=amount, bd=_sep(10)
        )
        total += amount
    await session.commit()
    return SimpleNamespace(
        total=total,
        table_ids={table_a.id, table_b.id},
        payment_methods={"Tiền mặt", "QR"},
    )


@pytest_asyncio.fixture
async def order_awaiting_reconciliation(session):
    order = await _r_order(session, bd=_sep(11), status="Chờ đối soát", order_type="Mang về")
    total = Decimal("120000")
    await _r_payment(session, order, method="QR", status="Chờ đối soát", amount=total, bd=_sep(11))
    await session.commit()
    return SimpleNamespace(total=total, order_id=order.id)


@pytest_asyncio.fixture
async def disputed_payment(session):
    """A transaction the manager refused to confirm — never settled into an invoice."""
    order = await _r_order(session, bd=_sep(12), status="Tranh chấp", order_type="Mang về")
    total = Decimal("90000")
    await _r_payment(session, order, method="QR", status="Tranh chấp", amount=total, bd=_sep(12))
    await session.commit()
    return SimpleNamespace(total=total, order_id=order.id)


@pytest_asyncio.fixture
async def orders_in_september(session):
    """Ranking data where the top seller by quantity is not the top by revenue."""
    by_quantity = await _r_dish(session, "Món số lượng")
    by_revenue = await _r_dish(session, "Món doanh thu")
    order = await _r_order(session, bd=_sep(13), order_type="Mang về")
    await _r_line(session, order, by_quantity, 5, 20000)
    await _r_line(session, order, by_revenue, 1, 300000)
    await session.commit()
    return SimpleNamespace(
        dish_names={by_quantity.name, by_revenue.name},
        top_by_quantity=by_quantity.name,
        top_by_revenue=by_revenue.name,
    )


@pytest_asyncio.fixture
async def order_with_cancelled_line(session):
    kept = await _r_dish(session, "Món giữ")
    dropped = await _r_dish(session, "Món đã hủy")
    order = await _r_order(session, bd=_sep(13), order_type="Mang về")
    await _r_line(session, order, kept, 1, 30000)
    await _r_line(session, order, dropped, 4, 30000, status="Đã hủy")
    await session.commit()
    return SimpleNamespace(order_id=order.id)


@pytest_asyncio.fixture
async def order_at_0130(session):
    """Placed at 01:30, so it belongs to the previous business date."""
    dish = await _r_dish(session, "Món khuya")
    placed_at = datetime(2026, 9, 25, 1, 30)
    order = await _r_order(
        session,
        bd=date(2026, 9, 24),
        order_type="Mang về",
        at=placed_at,
    )
    await _r_line(session, order, dish, 1, 40000)
    await session.commit()
    return SimpleNamespace(business_date=order.business_date, placed_at=placed_at)


@pytest_asyncio.fixture
async def september_data(session, write_off_in_september):
    """A closed September: revenue, consumed ingredients and the month's waste."""
    ingredient = await _r_ingredient(session, "NL September", Decimal("10000"))
    dish = await _r_dish(session, "Món September")
    recipe = await _r_recipe(session, dish, ingredient, Decimal("0.5"), _sep(1))
    order = await _r_order(session, bd=_sep(20), order_type="Mang về")
    await _r_line(session, order, dish, 4, 125000, recipe_id=recipe.id)
    revenue = Decimal("500000")
    await _r_invoice(session, order, bd=_sep(20), total=revenue)
    await session.commit()
    waste = write_off_in_september.value
    ingredients = Decimal("20000")  # 4 portions x 0.5kg x 10.000
    cogs = ingredients + waste
    return SimpleNamespace(
        revenue=revenue,
        cogs=cogs,
        waste=waste,
        margin=revenue - cogs,
        month=202609,
    )


@pytest_asyncio.fixture
async def order_before_recipe_change(session):
    ingredient = await _r_ingredient(session, "NL trước đổi", Decimal("10000"))
    dish = await _r_dish(session, "Món đổi công thức")
    recipe = await _r_recipe(session, dish, ingredient, Decimal("0.5"), _sep(1))
    order = await _r_order(session, bd=_sep(5), order_type="Mang về")
    await _r_line(session, order, dish, 2, 60000, recipe_id=recipe.id)
    await session.commit()
    return SimpleNamespace(expected_cost=Decimal("10000"))


@pytest_asyncio.fixture
async def order_after_recipe_change(session):
    ingredient = await _r_ingredient(session, "NL sau đổi", Decimal("10000"))
    dish = await _r_dish(session, "Món đổi công thức mới")
    recipe = await _r_recipe(session, dish, ingredient, Decimal("0.25"), _sep(15))
    order = await _r_order(session, bd=_sep(25), order_type="Mang về")
    await _r_line(session, order, dish, 2, 60000, recipe_id=recipe.id)
    await session.commit()
    return SimpleNamespace(expected_cost=Decimal("5000"))


@pytest_asyncio.fixture
async def cancelled_orders(session):
    dish = await _r_dish(session, "Món bị hủy")
    orders = []
    for day, status, reason, quantity in (
        (14, "Đã hủy", "khách bỏ về", 2),
        (15, "Tự động đóng", "khách đổi ý", 1),
    ):
        order = await _r_order(
            session, bd=_sep(day), status=status, order_type="Mang về", reason=reason
        )
        await _r_line(session, order, dish, quantity, 45000, status="Đã hủy")
        orders.append(SimpleNamespace(total=Decimal(quantity) * Decimal(45000), reason=reason))
    await session.commit()
    return orders


@pytest_asyncio.fixture
async def write_off_in_september(session):
    ingredient = await _r_ingredient(session, "NL hao hụt", Decimal("10000"))
    value = Decimal("30000")
    await _r_issue(session, bd=_sep(22), ingredient=ingredient, quantity=Decimal("3"), cost=value)
    await session.commit()
    return SimpleNamespace(value=value)


@pytest_asyncio.fixture
async def write_off_before_month_close(session):
    ingredient = await _r_ingredient(session, "NL chưa tính giá", Decimal("10000"))
    await _r_issue(
        session, bd=_sep(23), ingredient=ingredient, quantity=Decimal("2"), cost=Decimal("0")
    )
    await session.commit()
    return SimpleNamespace(count=1)


@pytest_asyncio.fixture
async def write_off_after_backfill(session, write_off_before_month_close):
    from app.modules.inventory.costing import backfill_issue_costs

    updated = await backfill_issue_costs(session, 202609)
    await session.commit()
    assert updated == write_off_before_month_close.count
    return SimpleNamespace(count=0)


@pytest_asyncio.fixture
async def orders_in_two_months(session):
    august_dish = await _r_dish(session, "Món tháng 8")
    september_dish = await _r_dish(session, "Món tháng 9")
    august = await _r_order(session, bd=_aug(10), order_type="Mang về")
    await _r_line(session, august, august_dish, 2, 30000)
    september = await _r_order(session, bd=_sep(10), order_type="Mang về")
    await _r_line(session, september, september_dish, 1, 30000)
    await session.commit()
    return SimpleNamespace(left_month="2026-08", right_month="2026-09")


@pytest_asyncio.fixture
async def two_months(session):
    august_total = Decimal("100000")
    september_total = Decimal("150000")
    august_dish = await _r_dish(session, "Món doanh thu tháng 8")
    september_dish = await _r_dish(session, "Món doanh thu tháng 9")
    august = await _r_order(session, bd=_aug(10), status="Đã thanh toán", order_type="Mang về")
    await _r_line(session, august, august_dish, 1, august_total)
    await _r_invoice(session, august, bd=_aug(10), total=august_total)
    september = await _r_order(session, bd=_sep(10), status="Đã thanh toán", order_type="Mang về")
    await _r_line(session, september, september_dish, 1, september_total)
    await _r_invoice(session, september, bd=_sep(10), total=september_total)
    await session.commit()
    return SimpleNamespace(
        left_revenue=august_total,
        right_revenue=september_total,
        left_month="2026-08",
        right_month="2026-09",
    )


# --- Phase 6 assistant fixtures ---


@pytest.fixture
def quota_reached(fake_llm):
    """Spend the daily quota before the test runs, so no call reaches the model."""
    from app.core.config import get_settings
    from app.modules.ai.pipeline import generator
    from app.shared import business_date

    today = business_date.business_date_of(business_date.now()).isoformat()
    generator.set_daily_calls(today, get_settings().ai_daily_question_quota)
    return fake_llm


class _FakeResult:
    def __init__(self, factory) -> None:
        self._factory = factory

    def keys(self) -> list[str]:
        return list(self._factory.columns)

    def fetchall(self) -> list[tuple]:
        return list(self._factory.rows)


class _FakeConnection:
    def __init__(self, factory) -> None:
        self._factory = factory

    async def execute(self, statement):
        self._factory.executed.append(str(statement))
        if self._factory.error is not None:
            raise self._factory.error
        return _FakeResult(self._factory)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class _FakeEngine:
    def __init__(self, factory, url) -> None:
        self._factory = factory
        self._url = url

    def connect(self):
        return _FakeConnection(self._factory)

    async def dispose(self) -> None:
        self._factory.disposed += 1


class FakeEngineFactory:
    """Records which read-only URL each role opened and what ran on it (NFR-06)."""

    def __init__(self) -> None:
        self.urls: list[str] = []
        self.executed: list[str] = []
        self.rows: list[tuple] = []
        self.columns: list[str] = ["MaNguyenLieu", "TenNguyenLieu"]
        self.disposed = 0
        self.error: Exception | None = None

    def __call__(self, url: str) -> _FakeEngine:
        self.urls.append(url)
        return _FakeEngine(self, url)


@pytest.fixture
def fake_engine_factory(monkeypatch) -> FakeEngineFactory:
    from app.modules.ai.pipeline import executor

    factory = FakeEngineFactory()
    monkeypatch.setattr(executor, "_create_engine", factory)
    return factory


@pytest.fixture
def readonly_urls(monkeypatch):
    """Distinct per-role account URLs, so a test can prove they are not shared."""
    from app.core.config import get_settings

    monkeypatch.setenv("AI_READONLY_URL_MANAGER", "mysql+asyncmy://ai_manager@db/restaurant")
    monkeypatch.setenv("AI_READONLY_URL_CASHIER", "mysql+asyncmy://ai_cashier@db/restaurant")
    monkeypatch.setenv("AI_READONLY_URL_WAREHOUSE", "mysql+asyncmy://ai_warehouse@db/restaurant")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def ai_engine(fake_engine_factory, readonly_urls):
    """Fake execution layer with a plausible single-row result, for pipeline tests."""
    fake_engine_factory.columns = ["SoDon"]
    fake_engine_factory.rows = [(2,)]
    return fake_engine_factory


class _SlowLlm:
    def __init__(self, delay: float) -> None:
        self._delay = delay
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        time.sleep(self._delay)
        return "SELECT 1 AS n FROM vw_ai_thungan"


@pytest.fixture
def slow_llm(monkeypatch):
    """A model that stalls past a deliberately tiny response budget (NFR-02)."""
    from app.core.config import get_settings
    from app.modules.ai import llm
    from app.modules.ai.pipeline import generator

    monkeypatch.setenv("AI_RESPONSE_BUDGET_SECONDS", "0.05")
    get_settings.cache_clear()
    slow = _SlowLlm(0.4)
    llm.set_client(slow)
    generator.reset_state()
    yield slow
    llm.set_client(None)
    generator.reset_state()
    get_settings.cache_clear()
