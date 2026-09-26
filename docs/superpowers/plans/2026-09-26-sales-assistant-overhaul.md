# Sales Steps, SePay QR and Assistant Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the missing dish prices, turn the Sales screen into a three-step table-centric flow with SePay VietQR payments, and rebuild the AI assistant (history, structured answers, floating widget).

**Architecture:** Six phases in dependency order. Backend changes stay inside their existing modules (`catalog`, `sales`, `ai`) behind unchanged endpoints plus a few new ones; payment gateways become a small adapter package with the current simulator as default. The web side splits the two big screens into focused step/message components that share one data hook each.

**Tech Stack:** FastAPI, SQLAlchemy 2 async, pytest (sqlite in-memory), httpx; Next.js 16 App Router, React 19, Tailwind 4, Vitest + Testing Library.

**Specs:**
- `docs/superpowers/specs/2026-09-26-sales-steps-sepay-design.md` (phases A–C, F)
- `docs/superpowers/specs/2026-09-26-assistant-redesign-design.md` (phases D–E)

## Global Constraints

- Prerequisite: the graphite design-system changes already in the working tree are committed by the user before Task A1 (`git add apps/web docs/design && git commit -m "feat(web): switch to the graphite square design system"`).
- Commit steps run only inside a subagent-owned worktree, or after the user says to commit on their branch (user CLAUDE.md §6).
- No schema change, no migration (both specs §2).
- Every AI-generated SQL still passes `app.modules.ai.guard.validate_sql`; "Chạy lại" goes through `POST /assistant/chat`, never re-runs stored SQL.
- `AI_MAX_ROWS` 500, `AI_SQL_TIMEOUT_SECONDS` 3, `AI_MAX_SQL_ATTEMPTS` 2 unchanged.
- The data-scope note is produced by code, never by the model (business rule 16).
- Secrets (`SEPAY_WEBHOOK_API_KEY`, `SEPAY_API_TOKEN`) live only in `.env`; never logged, never returned to the client.
- Default `PAYMENT_GATEWAY=simulator`; the existing simulator webhook behaviour and tests stay green.
- Tests never touch the network; `httpx.MockTransport` for SePay.
- Web: user-visible strings in Vietnamese; code, identifiers, comments in English; only design tokens from `docs/design/tokens.md` (no raw Tailwind palette colours).
- Web: `useSearchParams` consumers are rendered inside `<Suspense>` so `next build` keeps prerendering the route.
- Do not use generated `PageProps`/`LayoutProps` (AGENTS.md).
- API commands: `cd apps/api && uv run pytest <path> -q`, `uv run ruff check <paths>`, `uv run mypy src`. Web: `cd apps/web && pnpm vitest run <path>`, `pnpm lint`, `pnpm typecheck`. Final gate: `make gate` at repo root.

## Review Focus

1. **An order with a cancelled line is paid** — the customer must be charged without the cancelled line. `_order_total` currently sums every line (`sales/payments.py:60`). Pinned in Task B2.
2. **SePay sends the same transfer twice, sends it after the QR expired, or money arrives for an order already paid in cash** — no second invoice, no status regression of a paid order. Pinned in Task B4.
3. **A dish without an active price is tapped on the POS** — it must not enter the cart at 0 ₫. Pinned in Task C2.
4. **A user opens `/assistant?session=<id>` of another user** — API answers 404, the screen shows an error and falls back to a new chat. Pinned in Tasks D4 and E3.
5. **The model returns JSON with wrong shapes** (string instead of list, more than 4 highlights, duplicate follow-ups, empty headline) — output is sanitised or falls back to plain text. Pinned in Task D1.

---

## Phase A — Dish prices

### Task A1: Return the active price for dishes and persist the price given on create

**Files:**
- Modify: `apps/api/src/app/modules/catalog/versions.py` (add `active_prices`)
- Modify: `apps/api/src/app/modules/catalog/router.py:100-125` (`list_dishes`), `:160-185` (`update_dish`), `:490-510` (`set_dish_visibility` response)
- Modify: `apps/api/src/app/modules/catalog/service.py:131-165` (`create_dish`)
- Test: `apps/api/tests/modules/test_catalog_dish_prices.py` (create)

**Interfaces:**
- Produces: `async def active_prices(session: AsyncSession, dish_ids: Sequence[int], bd: date) -> dict[int, Decimal]` in `app.modules.catalog.versions`. `GET /catalog/dishes` items carry `GiaHienTai: float | None`.

- [ ] **Step 1: Write the failing tests**

```python
"""Dish prices on the catalogue API match the price an order would snapshot."""

from decimal import Decimal

import pytest

from app.main import app
from app.modules.catalog.models import DishPriceVersion
from app.modules.catalog.versions import active_price_version, active_prices
from app.shared.enums import VersionStatus
from tests.helpers import today, tomorrow
from tests.modules.test_catalog_dishes import (
    _auth_headers,
    _make_client,
    create_dish,
    list_dishes,
)


def _version(dish_id: int, price: int, bd, status=VersionStatus.HIEU_LUC.value):
    return DishPriceVersion(
        dish_id=dish_id, price=price, business_date=bd, status=status, change_type="Tạo mới"
    )


async def _price_in_list(session, dish_name: str):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        resp = await list_dishes(client, headers)
    app.dependency_overrides.clear()
    return next(x["GiaHienTai"] for x in resp.json()["items"] if x["TenMon"] == dish_name)


@pytest.mark.asyncio
async def test_the_list_shows_the_active_price(session, dish):
    session.add(_version(dish.id, 65000, today()))
    await session.commit()

    assert await _price_in_list(session, "Phở bò") == 65000


@pytest.mark.asyncio
async def test_a_price_scheduled_for_tomorrow_is_not_shown_yet(session, dish):
    session.add(_version(dish.id, 65000, today()))
    session.add(_version(dish.id, 70000, tomorrow()))
    await session.commit()

    assert await _price_in_list(session, "Phở bò") == 65000


@pytest.mark.asyncio
async def test_a_dish_without_a_price_shows_none(session, dish):
    assert await _price_in_list(session, "Phở bò") is None


@pytest.mark.asyncio
async def test_batch_lookup_agrees_with_the_order_snapshot_lookup(session, three_dishes):
    first, second, third = three_dishes
    session.add(_version(first.id, 50000, today()))
    session.add(_version(first.id, 55000, today()))
    session.add(_version(second.id, 30000, today(), status="Hết hiệu lực"))
    await session.commit()

    batch = await active_prices(session, [d.id for d in three_dishes], today())

    for d in three_dishes:
        single = await active_price_version(session, d.id, today())
        expected = Decimal(str(single.price)) if single else None
        assert batch.get(d.id) == expected


@pytest.mark.asyncio
async def test_a_price_given_on_create_is_persisted(session, group):
    headers = await _auth_headers(session)
    async with await _make_client(session) as client:
        created = await create_dish(
            client, headers, name="Bún chả", group_id=group.id, GiaHienTai=60000
        )
        listed = await list_dishes(client, headers)
    app.dependency_overrides.clear()

    assert created.status_code == 201
    assert created.json()["GiaHienTai"] == 60000
    item = next(x for x in listed.json()["items"] if x["TenMon"] == "Bún chả")
    assert item["GiaHienTai"] == 60000
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd apps/api && uv run pytest tests/modules/test_catalog_dish_prices.py -q`
Expected: FAIL — `ImportError: cannot import name 'active_prices'`.

- [ ] **Step 3: Add `active_prices` to `catalog/versions.py`** (below `active_price`)

```python
async def active_prices(
    session: AsyncSession, dish_ids: Sequence[int], bd: date
) -> dict[int, Decimal]:
    """`active_price_version` for many dishes in one query; dishes without a price are absent."""
    if not dish_ids:
        return {}
    rows = await session.execute(
        select(DishPriceVersion)
        .where(
            DishPriceVersion.dish_id.in_(list(dish_ids)),
            DishPriceVersion.status == VersionStatus.HIEU_LUC.value,
            DishPriceVersion.business_date <= bd,
        )
        .order_by(
            DishPriceVersion.dish_id,
            DishPriceVersion.business_date.desc(),
            DishPriceVersion.id.desc(),
        )
    )
    prices: dict[int, Decimal] = {}
    for version in rows.scalars():
        prices.setdefault(version.dish_id, Decimal(str(version.price)))
    return prices
```

Add `from collections.abc import Sequence` to the imports.

- [ ] **Step 4: Use it in the router**

In `catalog/router.py` add imports `from app.modules.catalog.versions import active_price, active_prices` and `from app.shared import business_date` (skip any already present), then add below the router declaration:

```python
def _today():
    return business_date.business_date_of(business_date.now())


def _money(value) -> float | None:
    return float(value) if value is not None else None
```

`list_dishes`: after `sliced = ...` insert `prices = await active_prices(session, [d.id for d in sliced], _today())` and replace `GiaHienTai=None,` with `GiaHienTai=_money(prices.get(d.id)),`.

`update_dish` and the visibility handler: replace `GiaHienTai=None,` with `GiaHienTai=_money(await active_price(session, d.id, _today())),`.

- [ ] **Step 5: Persist the price in `create_dish`** (`catalog/service.py`)

Replace the placeholder comment line with:

```python
    if price is not None:
        # The price lives in LICH_SU_GIA_MON, the same table orders snapshot from.
        await apply_price_directly(session, actor_id, d.id, _Decimal(str(price)))
```

`apply_price_directly` and `_Decimal` are already defined in this module.

- [ ] **Step 6: Run the new and existing catalogue tests**

Run: `cd apps/api && uv run pytest tests/modules/test_catalog_dish_prices.py tests/modules/test_catalog_dishes.py tests/modules/test_catalog_prices.py -q`
Expected: all PASS.

- [ ] **Step 7: Lint and type-check**

Run: `cd apps/api && uv run ruff check src/app/modules/catalog tests/modules/test_catalog_dish_prices.py && uv run mypy src`
Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add apps/api/src/app/modules/catalog apps/api/tests/modules/test_catalog_dish_prices.py
git commit -m "fix(catalog): return the active dish price and persist the price given on create"
```

---

## Phase B — Sales API

### Task B1: Floor board endpoint

**Files:**
- Create: `apps/api/src/app/modules/sales/floor.py`
- Modify: `apps/api/src/app/modules/sales/router.py` (new route, import)
- Test: `apps/api/tests/modules/test_sales_floor.py` (create)

The spec names `service.py`; that file is only a re-export, and the module already splits by concern (`orders.py`, `payments.py`, `tickets.py`), so the logic goes in `floor.py`.

**Interfaces:**
- Produces: `async def floor_board(session: AsyncSession) -> dict[str, list[dict[str, Any]]]`; `GET /api/v1/sales/floor` →
  `{"tables": [{"MaBan", "TenBan", "TrangThai", "order": FloorOrder | None}], "takeaway": [FloorOrder]}`,
  `FloorOrder = {"MaOrder": int, "MaOrderHienThi": str | None, "MoLuc": str | None, "SoMon": int, "TamTinh": float}`.

- [ ] **Step 1: Write the failing tests**

```python
"""GET /sales/floor — tables with their open order, plus open takeaway orders."""

from decimal import Decimal

import pytest

from app.modules.catalog.models import DiningTable, Dish, DishGroup
from app.modules.sales.models import Order, OrderLine
from app.shared import business_date
from tests.modules.test_sales_payments import _headers, _make_client


async def _dish(session) -> Dish:
    group = DishGroup(name="Nhóm", display_order=1, is_deleted=False)
    session.add(group)
    await session.flush()
    dish = Dish(name="Phở bò", group_id=group.id, is_deleted=False)
    session.add(dish)
    await session.flush()
    return dish


async def _order(session, *, table_id, kind, code, lines, status="Đang mở") -> Order:
    order = Order(
        display_code=code,
        business_date=business_date.business_date_of(business_date.now()),
        table_id=table_id,
        order_type=kind,
        status=status,
        created_at=business_date.now(),
    )
    session.add(order)
    await session.flush()
    for dish_id, qty, price, line_status in lines:
        session.add(
            OrderLine(
                order_id=order.id,
                dish_id=dish_id,
                quantity=qty,
                unit_price=Decimal(price),
                status=line_status,
            )
        )
    await session.flush()
    return order


@pytest.mark.anyio
async def test_the_floor_lists_tables_open_orders_and_takeaway(session):
    dish = await _dish(session)
    free = DiningTable(name="Bàn 01", status="Trống", is_deleted=False)
    busy = DiningTable(name="Bàn 04", status="Đang phục vụ", is_deleted=False)
    gone = DiningTable(name="Bàn cũ", status="Trống", is_deleted=True)
    session.add_all([free, busy, gone])
    await session.flush()
    await _order(
        session,
        table_id=busy.id,
        kind="Tại chỗ",
        code="ORD-1",
        lines=[(dish.id, 2, "65000", "Chờ"), (dish.id, 1, "65000", "Đã hủy")],
    )
    await _order(
        session, table_id=None, kind="Mang về", code="ORD-2", lines=[(dish.id, 1, "45000", "Chờ")]
    )
    await _order(
        session,
        table_id=None,
        kind="Mang về",
        code="ORD-3",
        lines=[(dish.id, 1, "45000", "Chờ")],
        status="Đã thanh toán",
    )
    await session.commit()

    client = await _make_client(session)
    headers, _ = await _headers(session)
    resp = await client.get("/api/v1/sales/floor", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert [t["TenBan"] for t in body["tables"]] == ["Bàn 01", "Bàn 04"]
    assert body["tables"][0]["order"] is None
    busy_order = body["tables"][1]["order"]
    assert busy_order["MaOrderHienThi"] == "ORD-1"
    assert busy_order["SoMon"] == 2
    assert busy_order["TamTinh"] == 130000
    assert [o["MaOrderHienThi"] for o in body["takeaway"]] == ["ORD-2"]


@pytest.mark.anyio
async def test_the_warehouse_role_cannot_read_the_floor(session):
    client = await _make_client(session)
    headers, _ = await _headers(session, role="WAREHOUSE", username="kho01")
    resp = await client.get("/api/v1/sales/floor", headers=headers)
    assert resp.status_code == 403
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_floor.py -q`
Expected: FAIL — 404 for `/api/v1/sales/floor`.

- [ ] **Step 3: Implement `sales/floor.py`**

```python
"""Floor board for the POS: every table with its open order, plus open takeaway orders."""

from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import DiningTable
from app.modules.sales.models import Order, OrderLine
from app.modules.sales.orders import LINE_CANCELLED, OPEN_ORDER_STATUSES


def _summary(order: Order, totals: dict[int, tuple[int, Decimal]]) -> dict[str, Any]:
    quantity, amount = totals.get(order.id, (0, Decimal(0)))
    return {
        "MaOrder": order.id,
        "MaOrderHienThi": order.display_code,
        "MoLuc": order.created_at.isoformat() if order.created_at else None,
        "SoMon": quantity,
        "TamTinh": float(amount),
    }


async def floor_board(session: AsyncSession) -> dict[str, list[dict[str, Any]]]:
    tables = (
        (
            await session.execute(
                select(DiningTable)
                .where(DiningTable.is_deleted.is_(False))
                .order_by(DiningTable.id)
            )
        )
        .scalars()
        .all()
    )
    open_orders = (
        (
            await session.execute(
                select(Order).where(Order.status.in_(OPEN_ORDER_STATUSES)).order_by(Order.id)
            )
        )
        .scalars()
        .all()
    )
    totals: dict[int, tuple[int, Decimal]] = {}
    if open_orders:
        rows = await session.execute(
            select(
                OrderLine.order_id,
                func.coalesce(func.sum(OrderLine.quantity), 0),
                func.coalesce(func.sum(OrderLine.unit_price * OrderLine.quantity), 0),
            )
            .where(
                OrderLine.order_id.in_([o.id for o in open_orders]),
                OrderLine.status != LINE_CANCELLED,
            )
            .group_by(OrderLine.order_id)
        )
        totals = {
            order_id: (int(quantity), Decimal(str(amount))) for order_id, quantity, amount in rows
        }

    by_table = {o.table_id: o for o in open_orders if o.table_id is not None}
    return {
        "tables": [
            {
                "MaBan": table.id,
                "TenBan": table.name,
                "TrangThai": table.status,
                "order": _summary(by_table[table.id], totals) if table.id in by_table else None,
            }
            for table in tables
        ],
        "takeaway": [_summary(o, totals) for o in open_orders if o.table_id is None],
    }
```

- [ ] **Step 4: Add the route** in `sales/router.py` (change the import to `from app.modules.sales import floor, orders, payments`) and add above `@router.post("/orders", ...)`:

```python
@router.get("/floor")
async def get_floor(
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    return await floor.floor_board(session)
```

- [ ] **Step 5: Run the tests**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_floor.py -q`
Expected: PASS.

- [ ] **Step 6: Lint, type-check, commit**

```bash
cd apps/api && uv run ruff check src/app/modules/sales tests/modules/test_sales_floor.py && uv run mypy src
git add apps/api/src/app/modules/sales apps/api/tests/modules/test_sales_floor.py
git commit -m "feat(sales): add a floor board endpoint for the step-based POS"
```

### Task B2: Gateway package, shared `confirm_payment`, and cancelled lines out of the total

**Files:**
- Create: `apps/api/src/app/modules/sales/gateways/__init__.py`, `apps/api/src/app/modules/sales/gateways/simulator.py`
- Modify: `apps/api/src/app/modules/sales/payments.py`
- Test: `apps/api/tests/modules/test_sales_payments.py` (append)

**Interfaces:**
- Produces:
  - `app.modules.sales.gateways.simulator.sign(payload: str) -> str`, `verify(payload: str, signature: str) -> bool`
  - `payments.sign_payload(payload: str) -> str` (kept, delegates to `simulator.sign`)
  - `async def confirm_payment(session, payment: PaymentTransaction, *, bank_ref: str | None = None) -> dict` — caller has already locked the payment, checked it is pending and that the amount matches; returns `{"payment", "invoice"}`.
  - `async def to_reconciliation(session, payment: PaymentTransaction, *, bank_ref: str | None, action: str) -> None`
  - `async def order_total(session, order: Order) -> Decimal` (renamed from `_order_total`, excludes cancelled lines)

- [ ] **Step 1: Write the failing regression test** (append to `test_sales_payments.py`)

```python
@pytest.mark.anyio
async def test_a_cancelled_line_is_not_charged(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    r = await client.post(
        "/api/v1/sales/orders",
        json={"MaBan": t.id, "lines": [{"MaMon": d.id, "SoLuong": 1}, {"MaMon": d.id, "SoLuong": 1}]},
        headers=h,
    )
    oid = r.json()["MaOrder"]
    detail = (await client.get(f"/api/v1/sales/orders/{oid}", headers=h)).json()
    line_id = detail["lines"][1]["MaChiTietOrder"]
    cancel = await client.post(
        f"/api/v1/sales/orders/{oid}/lines/{line_id}/cancel",
        json={"reason": "Khách đổi món"},
        headers=h,
    )
    assert cancel.status_code == 200, cancel.text

    paid = await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)

    assert paid.json()["invoice"]["TongTien"] == 50000
```

If the cancel endpoint's body key differs, read `router.py:191-204` and use its key; the assertion stays.

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_payments.py::test_a_cancelled_line_is_not_charged -q`
Expected: FAIL — `assert 100000.0 == 50000`.

- [ ] **Step 3: Create the simulator gateway**

`gateways/__init__.py`:

```python
"""Payment gateway adapters. `simulator` is the default; `sepay` is chosen by PAYMENT_GATEWAY."""
```

`gateways/simulator.py`:

```python
"""Mock QR gateway: an HMAC-SHA256 over `"<payment_id>:<amount>"` with PAYMENT_WEBHOOK_SECRET."""

import hashlib
import hmac

from app.core.config import get_settings


def _secret() -> str:
    return get_settings().payment_webhook_secret or "test-secret"


def sign(payload: str) -> str:
    return hmac.new(_secret().encode(), payload.encode(), hashlib.sha256).hexdigest()


def verify(payload: str, signature: str) -> bool:
    return hmac.compare_digest(sign(payload), signature)
```

- [ ] **Step 4: Refactor `payments.py`**

1. Replace the module docstring's second paragraph with: `Gateway specifics live in app.modules.sales.gateways; this module owns the business flow shared by every gateway.`
2. Delete `_require_webhook_secret`, `_gateway_sign`, `_verify_signature`; remove the now-unused `hashlib`/`hmac` imports; add `from app.modules.sales.gateways import simulator` and `from app.modules.sales.orders import LINE_CANCELLED` (inside functions if an import cycle appears, as the module already does for `ensure_order_is_open`).
3. `sign_payload` body becomes `return simulator.sign(payload)`.
4. Rename `_order_total` to `order_total` (update every call site in the file) and filter cancelled lines:

```python
async def order_total(session: AsyncSession, order: Order) -> Decimal:
    lines = (
        (
            await session.execute(
                select(OrderLine).where(
                    OrderLine.order_id == order.id, OrderLine.status != LINE_CANCELLED
                )
            )
        )
        .scalars()
        .all()
    )
    return sum((Decimal(str(line.unit_price)) * int(line.quantity) for line in lines), Decimal(0))
```

5. Add the shared confirmation and reconciliation helpers above `handle_webhook`:

```python
async def confirm_payment(
    session: AsyncSession, payment: PaymentTransaction, *, bank_ref: str | None = None
) -> dict:
    """Settle a pending QR payment whose amount the caller has already checked."""
    order = await session.get(Order, payment.order_id)
    if order is None:
        raise NotFoundError("Order không tồn tại.")
    await session.execute(select(Order).where(Order.id == order.id).with_for_update())
    total = await order_total(session, order)
    payment.status = QR_SUCCESS
    if bank_ref is not None:
        payment.bank_ref = bank_ref
    await session.flush()
    invoice = await _issue_invoice(
        session, order, business_date_value=payment.business_date, total=total
    )
    _settle(order, "Đã thanh toán", business_date.now())
    await _free_table(session, order)
    await session.flush()
    return {"payment": payment, "invoice": invoice}


async def to_reconciliation(
    session: AsyncSession, payment: PaymentTransaction, *, bank_ref: str | None, action: str
) -> None:
    """Money arrived but cannot be matched automatically; a manager resolves it."""
    payment.status = QR_RECONCILING
    if bank_ref is not None:
        payment.bank_ref = bank_ref
    order = await session.get(Order, payment.order_id)
    if order is not None:
        _settle(order, QR_RECONCILING, business_date.now())
    session.add(
        SystemAuditLog(
            user_id=None,
            action=action,
            target_entity="GIAO_DICH_THANH_TOAN",
            target_id=str(payment.id),
        )
    )
    await session.flush()
```

6. In `handle_webhook`, replace `_verify_signature(...)` with `simulator.verify(...)`, and replace everything after the amount check (`now = ...` through the final `return`) with `return await confirm_payment(session, payment)`. Keep the existing amount check (`total = await order_total(session, order)` … `raise BusinessRuleError("Số tiền không khớp.")`) before it.

- [ ] **Step 5: Run every payment test**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_payments.py tests/modules/test_sales_reconciliation.py tests/seed -q`
Expected: all PASS, including the new regression test.

- [ ] **Step 6: Lint, type-check, commit**

```bash
cd apps/api && uv run ruff check src/app/modules/sales tests/modules/test_sales_payments.py && uv run mypy src
git add apps/api/src/app/modules/sales apps/api/tests/modules/test_sales_payments.py
git commit -m "fix(sales): stop charging cancelled lines and move gateway signing into an adapter"
```

### Task B3: SePay configuration and pure adapter functions

**Files:**
- Modify: `apps/api/src/app/core/config.py`
- Create: `apps/api/src/app/modules/sales/gateways/sepay.py`
- Modify: `.env.example` (repo root; read it first — the user has local edits in it)
- Test: `apps/api/tests/modules/test_sales_sepay_adapter.py` (create)

**Interfaces:**
- Produces (in `gateways/sepay.py`):
  - `@dataclass(frozen=True) class Transfer: sepay_id: str; direction: str; amount: Decimal; code: str | None; content: str; reference: str | None`
  - `payment_code(payment_id: int, prefix: str) -> str`
  - `qr_image_url(*, account: str, bank: str, amount: Decimal, code: str) -> str`
  - `api_key_matches(header: str | None, expected: str) -> bool`
  - `parse_transfer(body: dict[str, Any]) -> Transfer` (raises `ValueError` when `id` or `transferAmount` is missing)
  - `payment_id_of(transfer: Transfer, prefix: str) -> int | None`
  - `transfer_from_listing(item: dict[str, Any]) -> dict[str, Any]` (maps a `userapi/transactions/list` row to the webhook body shape)
  - `async def recent_transfers(*, api_url: str, token: str, account: str) -> list[dict[str, Any]]`; module attribute `_transport: httpx.AsyncBaseTransport | None = None` for tests.
- Settings fields: `payment_gateway: Literal["simulator", "sepay"] = "simulator"`, `sepay_bank_account: str = ""`, `sepay_bank_code: str = ""`, `sepay_account_name: str = ""`, `sepay_webhook_api_key: str = ""`, `sepay_api_token: str = ""`, `sepay_payment_prefix: str = "TT"`, `sepay_api_url: str = "https://my.sepay.vn/userapi"`.

- [ ] **Step 1: Write the failing tests**

```python
"""SePay adapter: QR URL, webhook parsing and API-key check (no network)."""

from decimal import Decimal

import httpx
import pytest

from app.core.config import get_settings
from app.modules.sales.gateways import sepay

WEBHOOK = {
    "id": 92704,
    "gateway": "Vietcombank",
    "transactionDate": "2026-09-26 14:02:37",
    "accountNumber": "0123499999",
    "code": None,
    "content": "NGUYEN VAN A chuyen tien TT388",
    "transferType": "in",
    "transferAmount": 340000,
    "accumulated": 19077000,
    "subAccount": None,
    "referenceCode": "MBVCB.3278907687",
    "description": "",
}


def test_the_qr_url_carries_account_bank_amount_and_code():
    url = sepay.qr_image_url(account="0123499999", bank="MBBank", amount=Decimal("340000.0000"), code="TT388")
    assert url.startswith("https://qr.sepay.vn/img?")
    assert "acc=0123499999" in url
    assert "bank=MBBank" in url
    assert "amount=340000" in url
    assert "des=TT388" in url


def test_the_payment_code_is_prefix_plus_id():
    assert sepay.payment_code(388, "TT") == "TT388"


def test_the_payment_id_comes_from_code_then_content():
    transfer = sepay.parse_transfer(WEBHOOK)
    assert sepay.payment_id_of(transfer, "TT") == 388
    with_code = sepay.parse_transfer({**WEBHOOK, "code": "TT12", "content": "khong co ma"})
    assert sepay.payment_id_of(with_code, "TT") == 12
    no_code = sepay.parse_transfer({**WEBHOOK, "content": "chuyen tien an trua"})
    assert sepay.payment_id_of(no_code, "TT") is None


def test_parse_reads_amount_direction_and_reference():
    transfer = sepay.parse_transfer(WEBHOOK)
    assert transfer.sepay_id == "92704"
    assert transfer.direction == "in"
    assert transfer.amount == Decimal("340000")
    assert transfer.reference == "MBVCB.3278907687"


def test_parse_refuses_a_body_without_id_or_amount():
    with pytest.raises(ValueError):
        sepay.parse_transfer({"content": "TT1"})


@pytest.mark.parametrize(
    ("header", "ok"),
    [("Apikey secret-key", True), ("apikey secret-key", True), ("Apikey wrong", False),
     ("Bearer secret-key", False), (None, False), ("", False)],
)
def test_the_api_key_check(header, ok):
    assert sepay.api_key_matches(header, "secret-key") is ok


def test_an_empty_expected_key_never_matches():
    assert sepay.api_key_matches("Apikey ", "") is False


def test_selecting_sepay_without_credentials_fails_at_startup(monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    get_settings.cache_clear()
    with pytest.raises(RuntimeError, match="SEPAY"):
        get_settings()


@pytest.mark.anyio
async def test_recent_transfers_reads_the_listing(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer tok"
        assert request.url.params["account_number"] == "0123499999"
        return httpx.Response(200, json={"status": 200, "transactions": [
            {"id": "5", "amount_in": "340000.00", "amount_out": "0.00",
             "transaction_content": "TT388", "reference_number": "FT1", "code": "TT388"}]})

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    rows = await sepay.recent_transfers(api_url="https://my.sepay.vn/userapi", token="tok", account="0123499999")

    body = sepay.transfer_from_listing(rows[0])
    assert body == {"id": "5", "transferType": "in", "transferAmount": "340000.00",
                    "code": "TT388", "content": "TT388", "referenceCode": "FT1"}
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_sepay_adapter.py -q`
Expected: FAIL — `ImportError: cannot import name 'sepay'`.

- [ ] **Step 3: Add settings** in `core/config.py` below `payment_webhook_secret` (add `from typing import Literal` if missing):

```python
    # PAYMENT_GATEWAY picks the QR adapter; the simulator stays the default for tests.
    payment_gateway: Literal["simulator", "sepay"] = "simulator"
    sepay_bank_account: str = ""
    sepay_bank_code: str = ""
    sepay_account_name: str = ""
    sepay_webhook_api_key: str = ""
    sepay_api_token: str = ""
    sepay_payment_prefix: str = "TT"
    sepay_api_url: str = "https://my.sepay.vn/userapi"
```

and in `get_settings()` before `return settings`:

```python
    if settings.payment_gateway == "sepay" and not (
        settings.sepay_bank_account and settings.sepay_bank_code and settings.sepay_webhook_api_key
    ):
        raise RuntimeError(
            "SEPAY_BANK_ACCOUNT, SEPAY_BANK_CODE and SEPAY_WEBHOOK_API_KEY must be set "
            "when PAYMENT_GATEWAY=sepay"
        )
```

- [ ] **Step 4: Implement `gateways/sepay.py`**

```python
"""SePay (VietQR bank transfer) adapter — pure helpers plus one read-only HTTP call.

SePay authenticates webhooks with `Authorization: Apikey <key>`, not a body signature,
so the endpoint must only be exposed over HTTPS.
"""

import hmac
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import urlencode

import httpx

QR_IMAGE_BASE = "https://qr.sepay.vn/img"

# Tests swap this for httpx.MockTransport; production uses the default transport.
_transport: httpx.AsyncBaseTransport | None = None


@dataclass(frozen=True)
class Transfer:
    sepay_id: str
    direction: str
    amount: Decimal
    code: str | None
    content: str
    reference: str | None


def payment_code(payment_id: int, prefix: str) -> str:
    return f"{prefix}{payment_id}"


def qr_image_url(*, account: str, bank: str, amount: Decimal, code: str) -> str:
    query = urlencode({"acc": account, "bank": bank, "amount": str(int(amount)), "des": code})
    return f"{QR_IMAGE_BASE}?{query}"


def api_key_matches(header: str | None, expected: str) -> bool:
    if not expected or not header:
        return False
    scheme, _, key = header.partition(" ")
    return scheme.lower() == "apikey" and hmac.compare_digest(key.strip(), expected)


def parse_transfer(body: dict[str, Any]) -> Transfer:
    if body.get("id") is None or body.get("transferAmount") is None:
        raise ValueError("SePay payload needs id and transferAmount")
    try:
        amount = Decimal(str(body["transferAmount"]))
    except InvalidOperation as exc:
        raise ValueError("transferAmount is not a number") from exc
    return Transfer(
        sepay_id=str(body["id"]),
        direction=str(body.get("transferType") or ""),
        amount=amount,
        code=body.get("code") or None,
        content=str(body.get("content") or ""),
        reference=body.get("referenceCode") or None,
    )


def payment_id_of(transfer: Transfer, prefix: str) -> int | None:
    pattern = re.compile(rf"{re.escape(prefix)}(\d+)", re.IGNORECASE)
    for text in (transfer.code or "", transfer.content):
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


def transfer_from_listing(item: dict[str, Any]) -> dict[str, Any]:
    amount_in = Decimal(str(item.get("amount_in") or "0"))
    return {
        "id": str(item.get("id")),
        "transferType": "in" if amount_in > 0 else "out",
        "transferAmount": item.get("amount_in"),
        "code": item.get("code"),
        "content": item.get("transaction_content") or "",
        "referenceCode": item.get("reference_number"),
    }


async def recent_transfers(*, api_url: str, token: str, account: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(transport=_transport, timeout=5.0) as client:
        response = await client.get(
            f"{api_url}/transactions/list",
            params={"account_number": account, "limit": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        response.raise_for_status()
        rows = response.json().get("transactions") or []
    return [row for row in rows if isinstance(row, dict)]
```

- [ ] **Step 5: Update `.env.example`** — read it first, then append (keep the user's existing edits):

```
# QR payments: simulator (default, tests) or sepay (VietQR via SePay Test mode)
PAYMENT_GATEWAY=simulator
SEPAY_BANK_ACCOUNT=
SEPAY_BANK_CODE=
SEPAY_ACCOUNT_NAME=
SEPAY_WEBHOOK_API_KEY=
SEPAY_API_TOKEN=
SEPAY_PAYMENT_PREFIX=TT
```

- [ ] **Step 6: Run the tests, lint, type-check**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_sepay_adapter.py -q && uv run ruff check src tests/modules/test_sales_sepay_adapter.py && uv run mypy src`
Expected: PASS, no lint or type errors.

- [ ] **Step 7: Commit**

```bash
git add apps/api/src/app/core/config.py apps/api/src/app/modules/sales/gateways/sepay.py apps/api/tests/modules/test_sales_sepay_adapter.py .env.example
git commit -m "feat(sales): add the SePay VietQR adapter and its configuration"
```

### Task B4: SePay webhook, QR details on the QR endpoints, and "check" endpoint

**Files:**
- Modify: `apps/api/src/app/modules/sales/payments.py` (add `qr_fields`, `handle_sepay_transfer`, `check_payment`)
- Modify: `apps/api/src/app/modules/sales/router.py` (`start_order_qr`, `list payments` at `:302`, new `POST /webhooks/sepay`, new `POST /payments/{payment_id}/check`)
- Test: `apps/api/tests/modules/test_sales_sepay_webhook.py` (create)

**Interfaces:**
- Consumes: B2 `confirm_payment`, `to_reconciliation`, `order_total`; B3 `sepay.*`, settings fields.
- Produces:
  - `async def qr_fields(session, payment: PaymentTransaction) -> dict[str, Any]` — `{}` for the simulator; otherwise `{"qr_image_url", "payment_code", "bank_code", "bank_account", "account_name"}`.
  - `async def handle_sepay_transfer(session, body: dict[str, Any]) -> str` → one of `"confirmed" | "duplicate" | "ignored" | "unmatched" | "reconciling"`.
  - `async def check_payment(session, payment_id: int) -> PaymentTransaction`.
  - HTTP: `POST /api/v1/sales/webhooks/sepay` → `{"success": true}`; `POST /api/v1/sales/payments/{id}/check` → `{"MaGiaoDich", "TrangThai"}`; QR responses gain the `qr_fields` keys.

- [ ] **Step 1: Write the failing tests**

```python
"""SePay webhook and QR details (FR-SALE-15/16 with the SePay adapter)."""

from datetime import timedelta

import httpx
import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.modules.sales.gateways import sepay
from app.shared import business_date
from tests.helpers import FIXED_NOW, order_status, payment_status
from tests.modules.test_sales_payments import _headers, _make_client, _setup, _submit

HOOK = "/api/v1/sales/webhooks/sepay"


@pytest.fixture
def sepay_env(monkeypatch):
    monkeypatch.setenv("PAYMENT_GATEWAY", "sepay")
    monkeypatch.setenv("SEPAY_BANK_ACCOUNT", "0123499999")
    monkeypatch.setenv("SEPAY_BANK_CODE", "MBBank")
    monkeypatch.setenv("SEPAY_ACCOUNT_NAME", "NHA HANG DEMO")
    monkeypatch.setenv("SEPAY_WEBHOOK_API_KEY", "hook-key")
    monkeypatch.setenv("SEPAY_API_TOKEN", "api-token")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _body(payment_id: int, amount: int, sepay_id: int = 1, direction: str = "in") -> dict:
    return {"id": sepay_id, "transferType": direction, "transferAmount": amount,
            "code": None, "content": f"chuyen khoan TT{payment_id}", "referenceCode": "FT1"}


AUTH = {"Authorization": "Apikey hook-key"}


async def _qr(session):
    d, t = await _setup(session)
    client = await _make_client(session)
    h, _ = await _headers(session)
    oid = await _submit(session, client, h, d, t)
    r = await client.post(f"/api/v1/sales/orders/{oid}/pay/qr", headers=h)
    return client, h, oid, r


async def _invoices(session, oid) -> int:
    rr = await session.execute(text("SELECT COUNT(*) FROM HOA_DON WHERE MaOrder=:id"), {"id": oid})
    return rr.scalar_one()


@pytest.mark.anyio
async def test_the_qr_response_carries_the_vietqr_details(session, sepay_env):
    _, _, _, r = await _qr(session)
    body = r.json()
    assert body["payment_code"] == f"TT{body['MaGiaoDich']}"
    assert "amount=50000" in body["qr_image_url"]
    assert body["bank_account"] == "0123499999"


@pytest.mark.anyio
async def test_a_matching_transfer_settles_the_order(session, sepay_env):
    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    resp = await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)
    assert resp.status_code == 200
    assert resp.json() == {"success": True}
    assert await payment_status(session, oid) == "Thành công"
    assert await order_status(session, oid) == "Đã thanh toán"


@pytest.mark.anyio
async def test_a_wrong_api_key_is_rejected(session, sepay_env):
    client, _, oid, r = await _qr(session)
    resp = await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 50000),
                             headers={"Authorization": "Apikey nope"})
    assert resp.status_code == 401
    assert await order_status(session, oid) == "Đang mở"


@pytest.mark.anyio
async def test_the_same_transfer_twice_issues_one_invoice(session, sepay_env):
    client, _, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    await client.post(HOOK, json=_body(pid, 50000, sepay_id=7), headers=AUTH)
    second = await client.post(HOOK, json=_body(pid, 50000, sepay_id=7), headers=AUTH)
    assert second.status_code == 200
    assert await _invoices(session, oid) == 1


@pytest.mark.anyio
async def test_an_outgoing_transfer_is_ignored(session, sepay_env):
    client, _, oid, r = await _qr(session)
    await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 50000, direction="out"), headers=AUTH)
    assert await order_status(session, oid) == "Đang mở"


@pytest.mark.anyio
async def test_a_transfer_without_our_code_is_acknowledged_but_not_applied(session, sepay_env):
    client, _, oid, _ = await _qr(session)
    body = {**_body(0, 50000), "content": "tien an trua"}
    resp = await client.post(HOOK, json=body, headers=AUTH)
    assert resp.json() == {"success": True}
    assert await order_status(session, oid) == "Đang mở"


@pytest.mark.anyio
async def test_a_wrong_amount_goes_to_reconciliation(session, sepay_env):
    client, _, oid, r = await _qr(session)
    await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 40000), headers=AUTH)
    assert await order_status(session, oid) == "Chờ đối soát"
    assert await _invoices(session, oid) == 0


@pytest.mark.anyio
async def test_a_transfer_after_expiry_goes_to_reconciliation(session, sepay_env, monkeypatch):
    client, _, oid, r = await _qr(session)
    monkeypatch.setattr(business_date, "now", lambda: FIXED_NOW + timedelta(minutes=11))
    await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 50000), headers=AUTH)
    assert await order_status(session, oid) == "Chờ đối soát"


@pytest.mark.anyio
async def test_money_for_an_order_already_paid_in_cash_changes_nothing(session, sepay_env):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]
    await client.post(f"/api/v1/sales/payments/{pid}/cancel", headers=h)
    await client.post(f"/api/v1/sales/orders/{oid}/pay/cash", headers=h)
    await client.post(HOOK, json=_body(pid, 50000), headers=AUTH)
    assert await order_status(session, oid) == "Đã thanh toán"
    assert await _invoices(session, oid) == 1


@pytest.mark.anyio
async def test_check_confirms_through_the_transaction_listing(session, sepay_env, monkeypatch):
    client, h, oid, r = await _qr(session)
    pid = r.json()["MaGiaoDich"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"transactions": [
            {"id": "99", "amount_in": "50000.00", "amount_out": "0",
             "transaction_content": f"TT{pid}", "reference_number": "FT9", "code": f"TT{pid}"}]})

    monkeypatch.setattr(sepay, "_transport", httpx.MockTransport(handler))
    resp = await client.post(f"/api/v1/sales/payments/{pid}/check", headers=h)

    assert resp.status_code == 200
    assert resp.json()["TrangThai"] == "Thành công"
    assert await order_status(session, oid) == "Đã thanh toán"


@pytest.mark.anyio
async def test_the_sepay_hook_is_absent_under_the_simulator(session):
    client, _, _, r = await _qr(session)
    resp = await client.post(HOOK, json=_body(r.json()["MaGiaoDich"], 50000), headers=AUTH)
    assert resp.status_code == 404
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_sales_sepay_webhook.py -q`
Expected: FAIL — 404/`KeyError: 'payment_code'`.

- [ ] **Step 3: Add the service functions to `payments.py`**

Add imports `from typing import Any`, `from app.modules.sales.gateways import sepay`.

```python
async def qr_fields(session: AsyncSession, payment: PaymentTransaction) -> dict[str, Any]:
    settings = get_settings()
    if settings.payment_gateway != "sepay" or payment.method != "QR":
        return {}
    code = sepay.payment_code(payment.id, settings.sepay_payment_prefix)
    return {
        "qr_image_url": sepay.qr_image_url(
            account=settings.sepay_bank_account,
            bank=settings.sepay_bank_code,
            amount=Decimal(str(payment.amount)),
            code=code,
        ),
        "payment_code": code,
        "bank_code": settings.sepay_bank_code,
        "bank_account": settings.sepay_bank_account,
        "account_name": settings.sepay_account_name,
    }


async def handle_sepay_transfer(session: AsyncSession, body: dict[str, Any]) -> str:
    settings = get_settings()
    try:
        transfer = sepay.parse_transfer(body)
    except ValueError:
        logger.warning("Ignored a SePay payload without id or amount")
        return "ignored"
    if transfer.direction != "in":
        return "ignored"

    bank_ref = f"sepay:{transfer.sepay_id}"
    seen = (
        await session.execute(
            select(PaymentTransaction.id).where(PaymentTransaction.bank_ref == bank_ref)
        )
    ).first()
    if seen is not None:
        return "duplicate"

    payment_id = sepay.payment_id_of(transfer, settings.sepay_payment_prefix)
    payment = None
    if payment_id is not None:
        await expire_stale_qr(session)
        payment = (
            await session.execute(
                select(PaymentTransaction)
                .where(PaymentTransaction.id == payment_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
    if payment is None:
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_UNMATCHED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=bank_ref,
            )
        )
        await session.flush()
        return "unmatched"
    if payment.status == QR_SUCCESS:
        return "duplicate"

    order = await session.get(Order, payment.order_id)
    if order is None or order.status != "Đang mở":
        # Money for an order that is already settled or cancelled: record it for a human,
        # never reopen or re-invoice the order.
        payment.bank_ref = payment.bank_ref or bank_ref
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_UNMATCHED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id=str(payment.id),
            )
        )
        await session.flush()
        return "unmatched"

    total = await order_total(session, order)
    if payment.status == QR_PENDING and transfer.amount == total:
        await confirm_payment(session, payment, bank_ref=bank_ref)
        return "confirmed"
    await to_reconciliation(session, payment, bank_ref=bank_ref, action="WEBHOOK_NEEDS_RECONCILIATION")
    return "reconciling"


async def check_payment(session: AsyncSession, payment_id: int) -> PaymentTransaction:
    settings = get_settings()
    payment = await session.get(PaymentTransaction, payment_id)
    if payment is None:
        raise NotFoundError("Giao dịch không tồn tại.")
    if (
        settings.payment_gateway == "sepay"
        and settings.sepay_api_token
        and payment.status == QR_PENDING
    ):
        rows = await sepay.recent_transfers(
            api_url=settings.sepay_api_url,
            token=settings.sepay_api_token,
            account=settings.sepay_bank_account,
        )
        for row in rows:
            body = sepay.transfer_from_listing(row)
            transfer = sepay.parse_transfer(body)
            if sepay.payment_id_of(transfer, settings.sepay_payment_prefix) == payment.id:
                await handle_sepay_transfer(session, body)
                break
        await session.refresh(payment)
    return payment
```

- [ ] **Step 4: Wire the router**

Add `Request` to the FastAPI import, `from app.core.config import get_settings`, `from app.core.errors import NotFoundError, UnauthenticatedError`, `from app.modules.sales.gateways import sepay`, `from app.shared.audit import SystemAuditLog` (skip duplicates).

`start_order_qr` return becomes `{..., **(await payments.qr_fields(session, payment))}` (merge after the existing four keys).

In the payments list handler (`router.py:302`), merge `**(await payments.qr_fields(session, p))` into each item whose `TrangThai` is `"Chờ xác nhận"` (read the handler first; keep its existing keys).

Add below `webhook_payment`:

```python
@router.post("/webhooks/sepay")
async def webhook_sepay(request: Request, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    if settings.payment_gateway != "sepay":
        raise NotFoundError("Không tìm thấy.")
    if not sepay.api_key_matches(
        request.headers.get("Authorization"), settings.sepay_webhook_api_key
    ):
        session.add(
            SystemAuditLog(
                user_id=None,
                action="WEBHOOK_REJECTED",
                target_entity="GIAO_DICH_THANH_TOAN",
                target_id="sepay",
            )
        )
        await session.commit()
        raise UnauthenticatedError("API key không hợp lệ.")
    body = await request.json()
    await payments.handle_sepay_transfer(session, body if isinstance(body, dict) else {})
    await session.commit()
    return {"success": True}


@router.post("/payments/{payment_id}/check")
async def check_payment(
    payment_id: int,
    session: AsyncSession = Depends(get_session),
    user: Principal = Depends(require_roles(Role.MANAGER, Role.CASHIER)),
):
    payment = await payments.check_payment(session, payment_id)
    await session.commit()
    return {"MaGiaoDich": payment.id, "TrangThai": payment.status}
```

- [ ] **Step 5: Run all sales tests**

Run: `cd apps/api && uv run pytest tests/modules -k "sales" -q`
Expected: all PASS.

- [ ] **Step 6: Lint, type-check, commit**

```bash
cd apps/api && uv run ruff check src tests/modules/test_sales_sepay_webhook.py && uv run mypy src
git add apps/api/src/app/modules/sales apps/api/tests/modules/test_sales_sepay_webhook.py
git commit -m "feat(sales): confirm VietQR transfers through the SePay webhook"
```

---

## Phase C — Sales web

Shared types for this phase live in `apps/web/src/features/sales/types.ts`:

```ts
export type SalesStep = "floor" | "order" | "pay" | "done";

export type FloorOrder = {
  MaOrder: number;
  MaOrderHienThi: string | null;
  MoLuc: string | null;
  SoMon: number;
  TamTinh: number;
};

export type FloorTable = {
  MaBan: number;
  TenBan: string;
  TrangThai: string;
  order: FloorOrder | null;
};

export type FloorBoard = { tables: FloorTable[]; takeaway: FloorOrder[] };
```

### Task C1: Floor step

**Files:**
- Create: `apps/web/src/features/sales/types.ts` (content above), `apps/web/src/features/sales/floor-step.tsx`
- Modify: `apps/web/src/lib/status.ts` (`"Đã đặt": "neutral"`), `docs/design/tokens.md` §2.3 (move `bàn Đã đặt` from `primary` to `neutral`)
- Test: `apps/web/src/features/sales/floor-step.test.tsx` (create)

**Interfaces:**
- Produces: `FloorStep({ onNewOrder(tableId: number | null): void; onAddMore(orderId: number, tableId: number | null): void; onPay(orderId: number, tableId: number | null): void })`.

- [ ] **Step 1: Write the failing test**

```tsx
import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { FloorStep } from "./floor-step";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const board = {
  tables: [
    { MaBan: 1, TenBan: "Bàn 01", TrangThai: "Trống", order: null },
    {
      MaBan: 4,
      TenBan: "Bàn 04",
      TrangThai: "Đang phục vụ",
      order: { MaOrder: 142, MaOrderHienThi: "ORD-142", MoLuc: "2026-09-26T14:32:00", SoMon: 4, TamTinh: 248000 },
    },
  ],
  takeaway: [{ MaOrder: 139, MaOrderHienThi: "ORD-139", MoLuc: null, SoMon: 2, TamTinh: 120000 }],
};

function setup() {
  const handlers = { onNewOrder: vi.fn(), onAddMore: vi.fn(), onPay: vi.fn() };
  render(<FloorStep {...handlers} />);
  return handlers;
}

describe("FloorStep", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(path.startsWith("/sales/floor") ? board : { items: [] }),
    );
  });

  it("opens a new order on a free table", async () => {
    const h = setup();
    fireEvent.click(await screen.findByRole("button", { name: /Bàn 01/ }));
    expect(h.onNewOrder).toHaveBeenCalledWith(1);
  });

  it("offers add-more and pay for a busy table with its running total", async () => {
    const h = setup();
    fireEvent.click(await screen.findByRole("button", { name: /Bàn 04/ }));
    expect(screen.getAllByText("248.000 ₫").length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: "Gọi thêm" }));
    expect(h.onAddMore).toHaveBeenCalledWith(142, 4);
    fireEvent.click(screen.getByRole("button", { name: "Thanh toán" }));
    expect(h.onPay).toHaveBeenCalledWith(142, 4);
  });

  it("starts and resumes takeaway orders", async () => {
    const h = setup();
    fireEvent.click(await screen.findByRole("button", { name: "Đơn mang về mới" }));
    expect(h.onNewOrder).toHaveBeenCalledWith(null);
    fireEvent.click(screen.getByRole("button", { name: /ORD-139/ }));
    expect(h.onPay).toHaveBeenCalledWith(139, null);
  });

  it("filters tables by status", async () => {
    setup();
    await screen.findByRole("button", { name: /Bàn 04/ });
    const filters = screen.getByRole("group", { name: "Lọc bàn" });
    fireEvent.click(within(filters).getByRole("button", { name: /Trống/ }));
    expect(screen.queryByRole("button", { name: /Bàn 04/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Bàn 01/ })).toBeInTheDocument();
  });

  it("looks up an order by code and opens its payment", async () => {
    const h = setup();
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path.startsWith("/sales/orders?code=")
          ? { items: [{ MaOrder: 77, MaBan: 3 }] }
          : board,
      ),
    );
    fireEvent.change(await screen.findByLabelText("Tra mã order"), { target: { value: "ORD-77" } });
    fireEvent.submit(screen.getByRole("search"));
    await vi.waitFor(() => expect(h.onPay).toHaveBeenCalledWith(77, 3));
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/web && pnpm vitest run src/features/sales/floor-step.test.tsx`
Expected: FAIL — cannot resolve `./floor-step`.

- [ ] **Step 3: Implement `floor-step.tsx`**

```tsx
"use client";

import { Plus, Search, ShoppingBag } from "lucide-react";
import { useState } from "react";

import { ErrorState, LoadingState, StatusBadge } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ApiError, apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";

import type { FloorBoard, FloorOrder, FloorTable } from "./types";

const FILTERS = [
  { key: "all", label: "Tất cả" },
  { key: "free", label: "Trống" },
  { key: "busy", label: "Có khách" },
  { key: "booked", label: "Đã đặt" },
] as const;
type FilterKey = (typeof FILTERS)[number]["key"];

const loadBoard = () => apiFetch<FloorBoard>("/sales/floor");

function kindOf(table: FloorTable): Exclude<FilterKey, "all"> {
  if (table.order) return "busy";
  return table.TrangThai === "Đã đặt" ? "booked" : "free";
}

function openedAt(order: FloorOrder): string {
  if (!order.MoLuc) return "";
  return new Date(order.MoLuc).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
}

export function FloorStep({
  onNewOrder,
  onAddMore,
  onPay,
}: {
  onNewOrder: (tableId: number | null) => void;
  onAddMore: (orderId: number, tableId: number | null) => void;
  onPay: (orderId: number, tableId: number | null) => void;
}) {
  const board = useResource(loadBoard);
  const [filter, setFilter] = useState<FilterKey>("all");
  const [selected, setSelected] = useState<number | null>(null);
  const [code, setCode] = useState("");
  const [lookupError, setLookupError] = useState<string | null>(null);

  if (board.status === "loading") return <LoadingState rows={6} />;
  if (board.status === "error") return <ErrorState message={board.message} onRetry={board.reload} />;

  const { tables, takeaway } = board.data;
  const counts = { all: tables.length, free: 0, busy: 0, booked: 0 };
  for (const t of tables) counts[kindOf(t)] += 1;
  const visible = tables.filter((t) => filter === "all" || kindOf(t) === filter);
  const active = tables.find((t) => t.MaBan === selected && t.order) ?? null;

  async function lookup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLookupError(null);
    const needle = code.trim();
    if (!needle) return;
    try {
      const found = await apiFetch<{ items: { MaOrder: number; MaBan: number | null }[] }>(
        `/sales/orders?code=${encodeURIComponent(needle)}&size=1`,
      );
      const order = found.items[0];
      if (!order) {
        setLookupError(`Không tìm thấy order ${needle}.`);
        return;
      }
      onPay(order.MaOrder, order.MaBan ?? null);
    } catch (error: unknown) {
      setLookupError(error instanceof ApiError ? error.message : "Không tra cứu được order.");
    }
  }

  return (
    <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_340px]">
      <div className="min-w-0 space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <form role="search" onSubmit={lookup} className="relative w-full sm:w-72">
            <Search className="absolute top-2.5 left-2.5 size-4 text-subtle" aria-hidden />
            <Input
              aria-label="Tra mã order"
              placeholder="Tra mã order, ví dụ ORD-260926-142"
              className="pl-8"
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </form>
          <div role="group" aria-label="Lọc bàn" className="inline-flex overflow-hidden rounded-control border border-border-strong">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                type="button"
                aria-pressed={filter === f.key}
                onClick={() => setFilter(f.key)}
                className={cn(
                  "h-9 px-3 font-semibold not-first:border-l not-first:border-border",
                  filter === f.key ? "bg-primary text-white" : "bg-surface hover:bg-surface-sunken",
                )}
              >
                {f.label} <span className="font-mono text-xs tabular-nums opacity-80">{counts[f.key]}</span>
              </button>
            ))}
          </div>
        </div>
        {lookupError && <p role="alert" className="text-danger-fg">{lookupError}</p>}

        <div className="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-2">
          {visible.map((table) => {
            const busy = table.order !== null;
            return (
              <button
                key={table.MaBan}
                type="button"
                aria-pressed={selected === table.MaBan}
                onClick={() => (busy ? setSelected(table.MaBan) : onNewOrder(table.MaBan))}
                className={cn(
                  "grid min-h-28 content-between gap-2 rounded-container border border-border bg-surface p-3 text-left transition-[border-color,box-shadow] hover:border-ink hover:shadow-lift",
                  busy && "shadow-[inset_0_3px_0_0_var(--color-ink)]",
                  selected === table.MaBan && "border-ink ring-1 ring-ink",
                )}
              >
                <span className="flex items-center justify-between gap-2 text-lg font-bold tracking-tight">
                  {table.TenBan}
                  <StatusBadge status={busy ? "Đang phục vụ" : table.TrangThai} />
                </span>
                {table.order ? (
                  <span className="grid gap-0.5 text-xs text-muted">
                    <span className="text-[15px] font-bold text-ink tabular-nums">{formatVnd(table.order.TamTinh)}</span>
                    <span>{table.order.SoMon} món · từ {openedAt(table.order)}</span>
                  </span>
                ) : (
                  <span className="text-xs text-muted">Chạm để mở order</span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      <aside className="space-y-3 lg:sticky lg:top-4">
        {active?.order && (
          <section aria-label={`Order ${active.TenBan}`} className="rounded-container border border-border bg-surface">
            <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
              <h2 className="text-base font-bold">{active.TenBan}</h2>
              <StatusBadge status="Đang phục vụ" />
            </header>
            <div className="space-y-3 p-4">
              <p className="font-mono text-xs text-subtle">
                {active.order.MaOrderHienThi} · mở {openedAt(active.order)} · {active.order.SoMon} món
              </p>
              <p className="flex items-baseline justify-between border-t border-border-strong pt-3 text-lg font-bold">
                <span>Tạm tính</span>
                <span className="tabular-nums">{formatVnd(active.order.TamTinh)}</span>
              </p>
              <div className="grid grid-cols-2 gap-2">
                <Button variant="secondary" size="pos" onClick={() => onAddMore(active.order!.MaOrder, active.MaBan)}>
                  <Plus />
                  Gọi thêm
                </Button>
                <Button size="pos" onClick={() => onPay(active.order!.MaOrder, active.MaBan)}>
                  Thanh toán
                </Button>
              </div>
            </div>
          </section>
        )}

        <section aria-label="Mang về" className="rounded-container border border-border bg-surface">
          <header className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
            <h2 className="text-base font-bold">Mang về</h2>
            <Button size="sm" onClick={() => onNewOrder(null)} aria-label="Đơn mang về mới">
              <ShoppingBag />
              Đơn mới
            </Button>
          </header>
          <div className="grid gap-1.5 p-3">
            {takeaway.length === 0 ? (
              <p className="px-1 py-2 text-muted">Chưa có đơn mang về đang mở.</p>
            ) : (
              takeaway.map((order) => (
                <button
                  key={order.MaOrder}
                  type="button"
                  onClick={() => onPay(order.MaOrder, null)}
                  className="flex items-center justify-between gap-2 rounded-control border border-border px-3 py-2.5 text-left hover:border-ink"
                >
                  <span>
                    <span className="block font-mono font-semibold">{order.MaOrderHienThi}</span>
                    <span className="text-xs text-subtle">{order.SoMon} món · {openedAt(order)}</span>
                  </span>
                  <span className="font-bold tabular-nums">{formatVnd(order.TamTinh)}</span>
                </button>
              ))
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}
```

`active.order!` is safe because `active` is only set for tables whose `order` is non-null; if the lint config forbids non-null assertions, bind `const order = active?.order` before the JSX and use `order` instead.

- [ ] **Step 4: Retone "Đã đặt"** — in `lib/status.ts` change `"Đã đặt": "primary",` to `"Đã đặt": "neutral",`; in `docs/design/tokens.md` §2.3 move "bàn `Đã đặt`" from the `primary` row to the `neutral` row.

- [ ] **Step 5: Run, lint, type-check**

Run: `cd apps/web && pnpm vitest run src/features/sales/floor-step.test.tsx && pnpm lint && pnpm typecheck`
Expected: PASS, no errors.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/sales/types.ts apps/web/src/features/sales/floor-step.tsx apps/web/src/features/sales/floor-step.test.tsx apps/web/src/lib/status.ts docs/design/tokens.md
git commit -m "feat(sales): add the floor step with table status and takeaway orders"
```

### Task C2: Order step (menu with prices, new and add-more orders)

**Files:**
- Rename: `apps/web/src/features/sales/order-screen.tsx` → `order-step.tsx` (`git mv`), then edit
- Test: `apps/web/src/features/sales/order-step.test.tsx` (create); remove the `describe("OrderScreen", …)` block and the `OrderScreen` import from `payment-panel.test.tsx`

**Interfaces:**
- Consumes: C1 nothing directly.
- Produces: `OrderStep({ tableId: number | null; orderId: number | null; onBack(): void; onSent(orderId: number, next: "floor" | "pay"): void })`.

- [ ] **Step 1: Write the failing tests**

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { OrderStep } from "./order-step";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;

const dishes = {
  items: [
    { MaMon: 5, TenMon: "Phở bò", TrangThai: "Hoạt động", GiaHienTai: 65000, MaNhomMon: 1 },
    { MaMon: 6, TenMon: "Nem rán", TrangThai: "Hoạt động", GiaHienTai: null, MaNhomMon: 1 },
    { MaMon: 7, TenMon: "Bún chả", TrangThai: "Hết nguyên liệu", GiaHienTai: 60000, MaNhomMon: 1 },
  ],
};

function route(extra: Record<string, unknown> = {}) {
  const routes: Record<string, unknown> = {
    "/catalog/tables": [{ MaBan: 4, TenBan: "Bàn 04" }],
    "/catalog/dishes": dishes,
    "/catalog/groups": [{ MaNhomMon: 1, TenNhom: "Món chính" }],
    ...extra,
  };
  fetchMock.mockImplementation((path: string) =>
    Promise.resolve(Object.entries(routes).find(([p]) => path.startsWith(p))?.[1] ?? {}),
  );
}

describe("OrderStep", () => {
  beforeEach(() => vi.resetAllMocks());

  it("shows prices and keeps unpriced and unsellable dishes out of the cart", async () => {
    route();
    render(<OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={vi.fn()} />);

    expect(await screen.findByText("65.000 ₫")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Nem rán/ })).toBeDisabled();
    expect(screen.getByText("Chưa có giá")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Bún chả/ })).not.toBeInTheDocument();
  });

  it("totals the cart as dishes are added", async () => {
    route();
    render(<OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={vi.fn()} />);
    const tile = await screen.findByRole("button", { name: /Phở bò/ });
    fireEvent.click(tile);
    fireEvent.click(tile);
    expect(screen.getByTestId("cart-total")).toHaveTextContent("130.000 ₫");
  });

  it("creates a new dine-in order and moves on to payment", async () => {
    const onSent = vi.fn();
    route({ "/sales/orders": { MaOrder: 42, MaOrderHienThi: "ORD-42", rejected: [] } });
    render(<OrderStep tableId={4} orderId={null} onBack={vi.fn()} onSent={onSent} />);
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp & thanh toán" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(42, "pay"));
    expect(fetchMock).toHaveBeenCalledWith("/sales/orders", expect.objectContaining({
      method: "POST",
      body: expect.objectContaining({ MaBan: 4, LoaiDon: "Tại chỗ" }),
    }));
  });

  it("adds lines to an open order instead of creating one", async () => {
    const onSent = vi.fn();
    route({
      "/sales/orders/142/lines": { MaChiTietOrder: 9 },
      "/sales/orders/142": {
        MaOrder: 142, MaOrderHienThi: "ORD-142", TrangThai: "Đang mở",
        lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 2, DonGia: 65000, TrangThai: "Chờ" }],
      },
    });
    render(<OrderStep tableId={4} orderId={142} onBack={vi.fn()} onSent={onSent} />);

    expect(await screen.findByText("Đã gửi bếp")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));

    await vi.waitFor(() => expect(onSent).toHaveBeenCalledWith(142, "floor"));
    expect(fetchMock).toHaveBeenCalledWith("/sales/orders/142/lines", expect.objectContaining({
      method: "POST",
      body: { MaMon: 5, SoLuong: 1, GhiChu: null },
    }));
  });

  it("creates a takeaway order when there is no table", async () => {
    route({ "/sales/orders": { MaOrder: 50, MaOrderHienThi: "ORD-50", rejected: [] } });
    render(<OrderStep tableId={null} orderId={null} onBack={vi.fn()} onSent={vi.fn()} />);
    fireEvent.click(await screen.findByRole("button", { name: /Phở bò/ }));
    fireEvent.click(screen.getByRole("button", { name: "Gửi bếp" }));
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith("/sales/orders", expect.objectContaining({
        body: expect.objectContaining({ MaBan: null, LoaiDon: "Mang về" }),
      })),
    );
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/web && git mv src/features/sales/order-screen.tsx src/features/sales/order-step.tsx && pnpm vitest run src/features/sales/order-step.test.tsx`
Expected: FAIL — `OrderStep` is not exported.

- [ ] **Step 3: Rewrite the component contract in `order-step.tsx`**

Keep the existing imports, `Dish`, `Group`, `CartLine`, `CreatedOrder`, `UNSELLABLE`, `messageOf`, the dish grid JSX and the cart line JSX. Make these changes:

1. Delete `ORDER_TYPES`, the `Chip` component, the `DiningTable` table chips, `tableId`/`orderType`/`created` state and the "Loại đơn"/"Bàn" fieldsets.
2. Add types and loaders:

```tsx
type SentLine = { MaChiTietOrder: number; MaMon: number; SoLuong: number; DonGia: number; TrangThai: string };
type OpenOrder = { MaOrder: number; MaOrderHienThi: string | null; TrangThai: string; lines?: SentLine[] };

async function loadMenu(orderId: number | null) {
  const [tables, dishPage, groups, order] = await Promise.all([
    apiFetch<{ MaBan: number; TenBan: string }[]>("/catalog/tables"),
    apiFetch<{ items: Dish[] }>("/catalog/dishes?size=200"),
    apiFetch<Group[]>("/catalog/groups").catch(() => []),
    orderId === null ? Promise.resolve(null) : apiFetch<OpenOrder>(`/sales/orders/${orderId}`),
  ]);
  const all = dishPage.items || [];
  return {
    tables: Array.isArray(tables) ? tables : [],
    names: new Map(all.map((d) => [d.MaMon, d.TenMon])),
    dishes: all.filter((d) => !UNSELLABLE.has(d.TrangThai ?? "")),
    groups: Array.isArray(groups) ? groups : [],
    order,
  };
}
```

3. New signature and state:

```tsx
export function OrderStep({
  tableId,
  orderId,
  onBack,
  onSent,
}: {
  tableId: number | null;
  orderId: number | null;
  onBack: () => void;
  onSent: (orderId: number, next: "floor" | "pay") => void;
}) {
  const fetcher = useCallback(() => loadMenu(orderId), [orderId]);
  const menu = useResource(fetcher);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [cart, setCart] = useState<CartLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
```

Add `useCallback` to the React import and `import { ArrowLeft, ChefHat } from "lucide-react";` plus `import { toast } from "sonner";` and `import { StatusBadge } from "@/components/page-states";`.

4. After the loading/error guards:

```tsx
  const { tables, dishes, groups, names, order } = menu.data;
  const tableName = tableId === null ? "Mang về" : (tables.find((t) => t.MaBan === tableId)?.TenBan ?? `Bàn #${tableId}`);
  const sent = (order?.lines ?? []).filter((l) => l.TrangThai !== "Đã hủy");
  const sentTotal = sent.reduce((sum, l) => sum + l.DonGia * l.SoLuong, 0);
  const newTotal = cart.reduce((sum, l) => sum + l.DonGia * l.SoLuong, 0);
```

5. `addDish` refuses unpriced dishes (first line of the function): `if (dish.GiaHienTai == null) return;` and uses `DonGia: dish.GiaHienTai`.

6. Replace `submit` with:

```tsx
  async function send(next: "floor" | "pay") {
    setError(null);
    if (cart.length === 0) {
      if (orderId !== null && next === "pay") onSent(orderId, "pay");
      else setError("Chưa chọn món nào.");
      return;
    }
    setSubmitting(true);
    try {
      let id = orderId;
      if (id === null) {
        const created = await apiFetch<CreatedOrder>("/sales/orders", {
          method: "POST",
          body: {
            MaBan: tableId,
            LoaiDon: tableId === null ? "Mang về" : "Tại chỗ",
            lines: cart.map((l) => ({ MaMon: l.MaMon, SoLuong: l.SoLuong, GhiChu: l.GhiChu || null })),
          },
        });
        id = created.MaOrder;
        const skipped = created.rejected?.length ?? 0;
        if (skipped > 0) toast.warning(`Bỏ qua ${skipped} món thiếu tồn kho.`);
        setCart([]);
      } else {
        // One line per request: a failure keeps the unsent lines in the cart.
        for (const line of [...cart]) {
          await apiFetch(`/sales/orders/${id}/lines`, {
            method: "POST",
            body: { MaMon: line.MaMon, SoLuong: line.SoLuong, GhiChu: line.GhiChu || null },
          });
          setCart((prev) => prev.filter((l) => l.MaMon !== line.MaMon));
        }
      }
      toast.success(`Đã gửi món của ${tableName} xuống bếp.`);
      onSent(id, next);
    } catch (e: unknown) {
      setError(messageOf(e, "Không gửi được món. Kiểm tra kết nối rồi thử lại."));
    } finally {
      setSubmitting(false);
    }
  }
```

7. Above the grid, render the context bar:

```tsx
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-container border border-border bg-surface px-3 py-2">
          <Button variant="ghost" size="sm" onClick={onBack}>
            <ArrowLeft />
            Sơ đồ bàn
          </Button>
          <span className="text-base font-bold">{tableName}</span>
          {order && <span className="font-mono text-xs text-subtle">{order.MaOrderHienThi}</span>}
        </div>
```

8. In each dish tile: render the price as `<span className="font-bold tabular-nums">{formatVnd(d.GiaHienTai)}</span>` when `d.GiaHienTai != null`, otherwise `<span className="text-subtle">Chưa có giá</span>`; set `disabled={d.GiaHienTai == null}` on the tile button plus `disabled:cursor-not-allowed disabled:bg-surface-sunken disabled:hover:border-border disabled:hover:shadow-none` classes.

9. Cart panel: heading `{order ? `Order ${tableName}` : tableName}`; before the new-lines list add a caps label `Món mới` when `cart.length > 0`; after it render the sent section:

```tsx
            {sent.length > 0 && (
              <div className="border-t border-border">
                <p className="px-4 pt-3 pb-1 text-[11px] font-bold tracking-wider text-subtle uppercase">Đã gửi bếp</p>
                <ul className="divide-y divide-border bg-surface-sunken">
                  {sent.map((l) => (
                    <li key={l.MaChiTietOrder} className="flex items-center justify-between gap-3 px-4 py-2.5">
                      <span>{l.SoLuong}× {names.get(l.MaMon) ?? `Món #${l.MaMon}`}</span>
                      <span className="flex items-center gap-2">
                        <StatusBadge status={l.TrangThai} />
                        <span className="font-semibold tabular-nums">{formatVnd(l.DonGia * l.SoLuong)}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
```

10. Footer totals and actions:

```tsx
          {sent.length > 0 && (
            <div className="flex justify-between text-muted">
              <span>Đã gửi bếp</span>
              <span className="tabular-nums">{formatVnd(sentTotal)}</span>
            </div>
          )}
          <div className="flex items-baseline justify-between">
            <span>Tổng cộng</span>
            <span data-testid="cart-total" className="text-2xl font-bold tracking-tight tabular-nums">
              {formatVnd(sentTotal + newTotal)}
            </span>
          </div>
          {error && (
            <p role="alert" className="flex items-start gap-1.5 text-danger-fg">
              <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
              {error}
            </p>
          )}
          <div className="grid grid-cols-[1fr_1.4fr] gap-2">
            <Button variant="secondary" size="pos" onClick={() => send("floor")} disabled={submitting}>
              <ChefHat />
              Gửi bếp
            </Button>
            <Button size="pos" onClick={() => send("pay")} disabled={submitting}>
              Gửi bếp &amp; thanh toán
            </Button>
          </div>
```

Remove imports that become unused (`CircleCheck`, `Badge`, `cn` if unused).

- [ ] **Step 4: Remove the old OrderScreen tests** from `payment-panel.test.tsx` (the whole `describe("OrderScreen", …)` block and `import { OrderScreen } from "./order-screen";`).

- [ ] **Step 5: Run, lint, type-check**

Run: `cd apps/web && pnpm vitest run src/features/sales && pnpm lint && pnpm typecheck`
Expected: PASS (the workspace still imports `OrderScreen`; Task C4 replaces it — until then fix the import in `sales-workspace.tsx` to `import { OrderStep } from "@/features/sales/order-step";` and render `<OrderStep tableId={null} orderId={null} onBack={() => {}} onSent={(id) => payNow(id)} />` so typecheck passes).

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/sales
git commit -m "feat(sales): show dish prices and add dishes to open orders in the order step"
```

### Task C3: Pay step, cash change, SePay QR and done step

**Files:**
- Modify: `apps/web/src/features/sales/payment-panel.tsx`
- Create: `apps/web/src/features/sales/done-step.tsx`
- Test: `apps/web/src/features/sales/payment-panel.test.tsx` (update + append), `apps/web/src/features/sales/done-step.test.tsx` (create)

**Interfaces:**
- Produces:
  - `PaymentPanel({ orderId: number; onPaid?: (summary: { change: number | null }) => void })`
  - `export function InvoicePreview(...)` (exported, unchanged body)
  - `DoneStep({ orderId: number; change: number | null; onFinish(): void })`
  - `export function quickAmounts(total: number): number[]` from `payment-panel.tsx`

- [ ] **Step 1: Update the existing QR tests and add new ones** (`payment-panel.test.tsx`)

Add a helper after `openOrder`:

```tsx
async function chooseQr() {
  fireEvent.click(await screen.findByRole("radio", { name: /QR chuyển khoản/ }));
  fireEvent.click(screen.getByRole("button", { name: "Tạo mã QR" }));
}
```

In "disables creating a new QR while one is still live" replace `fireEvent.click(await screen.findByText("Thanh toán QR"));` with `await chooseQr();`. In "counts the QR deadline down…" replace the `act(async () => { fireEvent.click(screen.getByText("Thanh toán QR")); });` block with `await act(async () => { await chooseQr(); });`.

Append:

```tsx
describe("PaymentPanel cash and SePay", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    clearSession();
  });

  const priced = {
    ...openOrder,
    lines: [{ MaChiTietOrder: 1, MaMon: 5, SoLuong: 2, DonGia: 170000, TrangThai: "Chờ" }],
  };

  it("computes change and only confirms once enough cash is given", async () => {
    const onPaid = vi.fn();
    stubByPath({ "/sales/orders/1/pay/cash": { MaHoaDon: 9 }, "/sales/orders/1": priced });
    render(<PaymentPanel orderId={1} onPaid={onPaid} />);

    const given = await screen.findByLabelText("Tiền khách đưa");
    fireEvent.change(given, { target: { value: "300000" } });
    expect(screen.getByRole("button", { name: /Xác nhận đã thu/ })).toBeDisabled();

    fireEvent.change(given, { target: { value: "500000" } });
    expect(screen.getByTestId("cash-change")).toHaveTextContent("160.000 ₫");
    fireEvent.click(screen.getByRole("button", { name: /Xác nhận đã thu/ }));

    await vi.waitFor(() => expect(onPaid).toHaveBeenCalledWith({ change: 160000 }));
  });

  it("offers exact and rounded quick amounts", async () => {
    const { quickAmounts } = await import("./payment-panel");
    expect(quickAmounts(340000)).toEqual([340000, 350000, 400000, 500000]);
    expect(quickAmounts(500000)).toEqual([500000]);
  });

  it("shows the VietQR image, bank details and transfer code", async () => {
    stubByPath({
      "/sales/orders/1/pay/qr": qr({
        qr_image_url: "https://qr.sepay.vn/img?acc=1&bank=MBBank&amount=340000&des=TT1",
        payment_code: "TT1",
        bank_code: "MBBank",
        bank_account: "0123499999",
        account_name: "NHA HANG DEMO",
      }),
      "/sales/orders/1": priced,
    });
    render(<PaymentPanel orderId={1} />);
    await chooseQr();

    expect(await screen.findByRole("img", { name: /Mã VietQR/ })).toHaveAttribute(
      "src",
      expect.stringContaining("qr.sepay.vn"),
    );
    expect(screen.getByText("TT1")).toBeInTheDocument();
    expect(screen.getByText("0123499999")).toBeInTheDocument();
  });

  it("reports the payment once polling sees it succeed", async () => {
    vi.useFakeTimers();
    try {
      const onPaid = vi.fn();
      const live = qr();
      let succeeded = false;
      fetchMock.mockImplementation((path: string) => {
        if (path.startsWith("/sales/orders/1/payments"))
          return Promise.resolve({ items: [succeeded ? { ...live, TrangThai: "Thành công" } : live] });
        if (path.startsWith("/sales/orders/1")) return Promise.resolve(priced);
        return Promise.resolve({});
      });
      render(<PaymentPanel orderId={1} onPaid={onPaid} />);
      await act(async () => {});
      succeeded = true;
      await act(async () => {
        vi.advanceTimersByTime(3000);
      });
      expect(onPaid).toHaveBeenCalledWith({ change: null });
    } finally {
      vi.useRealTimers();
    }
  });
});
```

`done-step.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { DoneStep } from "./done-step";

describe("DoneStep", () => {
  it("shows the invoice, the change and goes back to the floor", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      SoHoaDon: "88", TongTien: 340000, PhuongThucThanhToan: "Tiền mặt", SoLanIn: 1, lines: [],
    });
    const onFinish = vi.fn();
    render(<DoneStep orderId={1} change={160000} onFinish={onFinish} />);

    expect(await screen.findByText("88")).toBeInTheDocument();
    expect(screen.getByText("160.000 ₫")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Về sơ đồ bàn" }));
    expect(onFinish).toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/web && pnpm vitest run src/features/sales/payment-panel.test.tsx src/features/sales/done-step.test.tsx`
Expected: FAIL — no "QR chuyển khoản" radio, no `DoneStep`.

- [ ] **Step 3: Change `payment-panel.tsx`**

1. Extend `Payment` with `qr_image_url?: string; payment_code?: string; bank_code?: string; bank_account?: string; account_name?: string;`.
2. Add, above the component:

```tsx
const ROUNDING = [50_000, 100_000, 500_000];

/** Exact amount first, then the next round notes a customer is likely to hand over. */
export function quickAmounts(total: number): number[] {
  const values = new Set<number>([total]);
  for (const step of ROUNDING) values.add(Math.ceil(total / step) * step);
  return [...values].filter((v) => v >= total).sort((a, b) => a - b);
}

function digits(value: string): number {
  return Number(value.replace(/\D/g, "")) || 0;
}
```

3. Signature: `export function PaymentPanel({ orderId, onPaid }: { orderId: number; onPaid?: (summary: { change: number | null }) => void })`; new state `const [method, setMethod] = useState<"cash" | "qr">("cash");` and `const [given, setGiven] = useState("");`.
4. Poll the live QR (after the countdown effect):

```tsx
  useEffect(() => {
    if (!qr || qr.TrangThai !== "Chờ xác nhận") return;
    const id = setInterval(async () => {
      try {
        const list = await apiFetch<{ items: Payment[] }>(`/sales/orders/${orderId}/payments`);
        const current = list.items.find((p) => p.MaGiaoDich === qr.MaGiaoDich);
        if (!current) return;
        if (current.TrangThai === "Thành công") onPaid?.({ change: null });
        if (current.TrangThai !== qr.TrangThai) setQr({ ...qr, ...current });
      } catch {
        // A dropped poll is retried on the next tick.
      }
    }, 3000);
    return () => clearInterval(id);
  }, [qr, orderId, onPaid]);
```

5. `payCash` calls `onPaid?.({ change: digits(given) - total })` after `loadInvoice()`; add:

```tsx
  const checkQr = () => {
    if (!qr) return;
    return run(async () => {
      const result = await apiFetch<{ TrangThai: string }>(`/sales/payments/${qr.MaGiaoDich}/check`, {
        method: "POST",
        body: {},
      });
      setQr({ ...qr, TrangThai: result.TrangThai });
      if (result.TrangThai === "Thành công") onPaid?.({ change: null });
      else setMessage("Chưa thấy giao dịch. Chờ thêm hoặc kiểm tra lại sau.");
    }, "Không kiểm tra được giao dịch.");
  };
```

6. Replace the two-button grid with a method choice and panes:

```tsx
        <div role="radiogroup" aria-label="Phương thức thanh toán" className="grid grid-cols-2 gap-2">
          {([
            ["cash", "Tiền mặt", "Nhập tiền khách đưa, tính tiền thối", Banknote],
            ["qr", "QR chuyển khoản", "Khách quét mã, hệ thống tự xác nhận", QrCode],
          ] as const).map(([value, title, hint, Icon]) => (
            <label
              key={value}
              className={cn(
                "grid cursor-pointer gap-1 rounded-container border px-3.5 py-3 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-primary",
                method === value ? "border-ink bg-surface-sunken ring-1 ring-ink" : "border-border-strong bg-surface",
              )}
            >
              <input type="radio" name={`method-${orderId}`} value={value} checked={method === value}
                onChange={() => setMethod(value)} className="sr-only" />
              <span className="flex items-center gap-2 text-[15px] font-bold"><Icon className="size-4" aria-hidden />{title}</span>
              <span className="text-xs text-muted">{hint}</span>
            </label>
          ))}
        </div>

        {method === "cash" && (
          <div className="space-y-3">
            <Label htmlFor={`given-${orderId}`}>Tiền khách đưa</Label>
            <Input id={`given-${orderId}`} inputMode="numeric" className="h-12 text-xl font-bold tabular-nums"
              value={given} onChange={(e) => setGiven(e.target.value)} placeholder={formatVnd(total)} />
            <div className="flex flex-wrap gap-1.5">
              {quickAmounts(total).map((amount) => (
                <Button key={amount} variant="secondary" size="sm" onClick={() => setGiven(String(amount))}>
                  {amount === total ? "Vừa đủ" : formatVnd(amount)}
                </Button>
              ))}
            </div>
            <div className="flex items-baseline justify-between rounded-control bg-surface-sunken px-3.5 py-3">
              <span>Tiền thối</span>
              <span data-testid="cash-change" className="text-2xl font-bold tabular-nums">
                {digits(given) >= total ? formatVnd(digits(given) - total) : "—"}
              </span>
            </div>
            <Button size="pos" className="w-full" onClick={payCash} disabled={locked || digits(given) < total}>
              <CircleCheck />
              Xác nhận đã thu {formatVnd(total)}
            </Button>
          </div>
        )}

        {method === "qr" && !live && (
          <Button size="pos" className="w-full" onClick={createQr} disabled={locked || reconciling}>
            <QrCode />
            Tạo mã QR
          </Button>
        )}
```

and wrap the existing QR box in `{method === "qr" && qr && qr.TrangThai !== "Đã hủy" && (…)}`. Inside it, before the countdown, add:

```tsx
            {qr.qr_image_url && live && (
              <div className="grid gap-4 sm:grid-cols-[192px_minmax(0,1fr)] sm:items-center">
                <img src={qr.qr_image_url} alt={`Mã VietQR thanh toán ${formatVnd(total)}`}
                  className="size-48 rounded-control border border-border bg-white p-2" />
                <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1.5">
                  <dt className="text-muted">Ngân hàng</dt><dd className="font-semibold">{qr.bank_code}</dd>
                  <dt className="text-muted">Số tài khoản</dt><dd className="font-mono font-semibold">{qr.bank_account}</dd>
                  <dt className="text-muted">Chủ tài khoản</dt><dd className="font-semibold">{qr.account_name}</dd>
                  <dt className="text-muted">Nội dung</dt><dd className="font-mono text-base font-bold">{qr.payment_code}</dd>
                </dl>
                <p className="text-xs font-semibold text-warning-fg sm:col-span-2">Môi trường thử nghiệm SePay</p>
              </div>
            )}
```

and a `Kiểm tra lại` button (`<Button variant="secondary" size="sm" onClick={checkQr} disabled={!live}><RefreshCw />Kiểm tra lại</Button>`) next to "Hủy QR". Import `RefreshCw` from lucide and `cn` from `@/lib/utils`.
7. `export` the `InvoicePreview` function.

- [ ] **Step 4: Create `done-step.tsx`**

```tsx
"use client";

import { CircleCheck } from "lucide-react";
import { useCallback } from "react";

import { ErrorState, LoadingState } from "@/components/page-states";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api-client";
import { formatVnd } from "@/lib/format";
import { useResource } from "@/lib/use-resource";

import { InvoicePreview } from "./payment-panel";

type Invoice = Parameters<typeof InvoicePreview>[0]["invoice"];

export function DoneStep({ orderId, change, onFinish }: { orderId: number; change: number | null; onFinish: () => void }) {
  const fetcher = useCallback(() => apiFetch<Invoice>(`/sales/orders/${orderId}/invoice`), [orderId]);
  const invoice = useResource(fetcher);

  if (invoice.status === "loading") return <LoadingState rows={3} />;
  if (invoice.status === "error") return <ErrorState message={invoice.message} onRetry={invoice.reload} />;

  const data = invoice.data;
  return (
    <section className="mx-auto grid max-w-lg justify-items-center gap-4 rounded-container border border-border bg-surface p-7 text-center">
      <span className="grid size-14 place-items-center rounded-container bg-success-subtle text-success-fg">
        <CircleCheck className="size-7" aria-hidden />
      </span>
      <h2 className="text-2xl font-bold tracking-tight">Đã thanh toán</h2>
      <dl className="grid w-full grid-cols-[auto_1fr] gap-x-4 gap-y-2 rounded-control bg-surface-sunken p-4 text-left">
        <dt className="text-muted">Số hoá đơn</dt>
        <dd className="text-right font-mono font-semibold">{data.SoHoaDon}</dd>
        <dt className="text-muted">Phương thức</dt>
        <dd className="text-right font-semibold">{data.PhuongThucThanhToan ?? "—"}</dd>
        <dt className="text-muted">Tổng tiền</dt>
        <dd className="text-right font-semibold tabular-nums">{formatVnd(data.TongTien)}</dd>
        {change !== null && (
          <>
            <dt className="text-muted">Tiền thối</dt>
            <dd className="text-right font-semibold tabular-nums">{formatVnd(change)}</dd>
          </>
        )}
      </dl>
      <div className="w-full text-left">
        <InvoicePreview invoice={data} onReprint={() => invoice.reload()} />
      </div>
      <Button size="pos" onClick={onFinish}>Về sơ đồ bàn</Button>
    </section>
  );
}
```

If `InvoicePreview`'s `invoice` prop type is not reachable through `Parameters`, export the `InvoiceDetail` type from `payment-panel.tsx` and import it instead.

- [ ] **Step 5: Run, lint, type-check**

Run: `cd apps/web && pnpm vitest run src/features/sales && pnpm lint && pnpm typecheck`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/web/src/features/sales
git commit -m "feat(sales): add cash change, SePay VietQR and a done step to payment"
```

### Task C4: Stepper workspace with URL state

**Files:**
- Create: `apps/web/src/features/sales/sales-stepper.tsx`
- Modify: `apps/web/src/features/sales/sales-workspace.tsx` (rewrite), `apps/web/src/app/(app)/sales/page.tsx`
- Delete: `apps/web/src/features/sales/order-lookup.tsx`, `apps/web/src/features/sales/order-lookup.test.tsx` (replaced by the floor lookup, spec §6.1)
- Test: `apps/web/src/features/sales/sales-workspace.test.tsx` (create)

**Interfaces:**
- Consumes: `FloorStep` (C1), `OrderStep` (C2), `PaymentPanel`/`DoneStep` (C3), `OrderDetail` (existing, `orderId` prop).
- Produces: URL contract `/sales?step=order|pay|done&table=<MaBan>&order=<MaOrder>`.

- [ ] **Step 1: Write the failing test**

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const replace = vi.fn();
let search = "";
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/sales",
  useSearchParams: () => new URLSearchParams(search),
}));
vi.mock("./floor-step", () => ({
  FloorStep: (p: { onNewOrder: (t: number | null) => void; onPay: (o: number, t: number | null) => void }) => (
    <div>
      <button onClick={() => p.onNewOrder(4)}>mock-new</button>
      <button onClick={() => p.onPay(142, 4)}>mock-pay</button>
    </div>
  ),
}));
vi.mock("./order-step", () => ({ OrderStep: () => <p>order-step</p> }));
vi.mock("./order-detail", () => ({ OrderDetail: () => <p>order-detail</p> }));
vi.mock("./payment-panel", () => ({ PaymentPanel: () => <p>payment-panel</p> }));
vi.mock("./done-step", () => ({ DoneStep: () => <p>done-step</p> }));

import { SalesWorkspace } from "./sales-workspace";

describe("SalesWorkspace", () => {
  beforeEach(() => {
    replace.mockReset();
    search = "";
  });

  it("starts on the floor and keeps the next step in the URL", () => {
    render(<SalesWorkspace />);
    fireEvent.click(screen.getByText("mock-new"));
    expect(replace).toHaveBeenCalledWith("/sales?step=order&table=4");
    fireEvent.click(screen.getByText("mock-pay"));
    expect(replace).toHaveBeenCalledWith("/sales?step=pay&table=4&order=142");
  });

  it("restores the pay step from the URL", () => {
    search = "step=pay&table=4&order=142";
    render(<SalesWorkspace />);
    expect(screen.getByText("payment-panel")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Thanh toán/ })).toHaveAttribute("aria-current", "step");
  });

  it("does not allow jumping to payment without an order", () => {
    search = "step=order&table=4";
    render(<SalesWorkspace />);
    expect(screen.getByRole("button", { name: /Thanh toán/ })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /Chọn bàn/ }));
    expect(replace).toHaveBeenCalledWith("/sales");
  });
});
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/web && pnpm vitest run src/features/sales/sales-workspace.test.tsx`
Expected: FAIL.

- [ ] **Step 3: Create `sales-stepper.tsx`**

```tsx
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

import type { SalesStep } from "./types";

const STEPS: { key: Exclude<SalesStep, "done">; label: string }[] = [
  { key: "floor", label: "Chọn bàn" },
  { key: "order", label: "Gọi món" },
  { key: "pay", label: "Thanh toán" },
];
const ORDER: SalesStep[] = ["floor", "order", "pay", "done"];

export function SalesStepper({
  current,
  enabled,
  onGo,
}: {
  current: SalesStep;
  enabled: Record<Exclude<SalesStep, "done">, boolean>;
  onGo: (step: Exclude<SalesStep, "done">) => void;
}) {
  const index = ORDER.indexOf(current);
  return (
    <ol aria-label="Các bước bán hàng" className="flex overflow-hidden rounded-control border border-border-strong bg-surface">
      {STEPS.map((step, i) => {
        const isCurrent = i === Math.min(index, 2);
        const done = i < index;
        return (
          <li key={step.key} className="not-first:border-l not-first:border-border">
            <button
              type="button"
              aria-current={isCurrent ? "step" : undefined}
              disabled={!enabled[step.key]}
              onClick={() => onGo(step.key)}
              className={cn(
                "flex h-11 items-center gap-2.5 px-4 font-semibold text-muted disabled:cursor-not-allowed disabled:opacity-50",
                isCurrent && "bg-surface-sunken text-ink",
              )}
            >
              <span
                className={cn(
                  "grid size-[22px] place-items-center rounded-badge bg-surface-sunken text-xs font-bold ring-1 ring-border",
                  isCurrent && "bg-primary text-white ring-0",
                  done && "bg-success-subtle text-success-fg ring-0",
                )}
              >
                {done ? <Check className="size-3.5" aria-hidden /> : i + 1}
              </span>
              {step.label}
            </button>
          </li>
        );
      })}
    </ol>
  );
}
```

- [ ] **Step 4: Rewrite `sales-workspace.tsx`**

```tsx
"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

import { PageHeader } from "@/components/page-states";

import { DoneStep } from "./done-step";
import { FloorStep } from "./floor-step";
import { OrderDetail } from "./order-detail";
import { OrderStep } from "./order-step";
import { PaymentPanel } from "./payment-panel";
import { SalesStepper } from "./sales-stepper";
import type { SalesStep } from "./types";

const STEPS: SalesStep[] = ["floor", "order", "pay", "done"];

function numberParam(value: string | null): number | null {
  const n = Number(value);
  return value !== null && Number.isInteger(n) && n > 0 ? n : null;
}

export function SalesWorkspace() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const [change, setChange] = useState<number | null>(null);

  const tableId = numberParam(params.get("table"));
  const orderId = numberParam(params.get("order"));
  const requested = (params.get("step") ?? "floor") as SalesStep;
  // A step that lacks what it needs falls back to the floor instead of rendering empty.
  const step: SalesStep =
    STEPS.includes(requested) && (requested === "floor" || requested === "order" || orderId !== null)
      ? requested
      : "floor";

  function go(next: SalesStep, table: number | null = tableId, order: number | null = orderId) {
    const query = new URLSearchParams();
    if (next !== "floor") {
      query.set("step", next);
      if (table !== null) query.set("table", String(table));
      if (order !== null) query.set("order", String(order));
    }
    const text = query.toString();
    router.replace(text ? `${pathname}?${text}` : pathname);
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeader title="Bán hàng" />
        <SalesStepper
          current={step}
          enabled={{ floor: true, order: step !== "floor" && step !== "done", pay: orderId !== null && step !== "done" }}
          onGo={(next) => go(next)}
        />
      </div>

      {step === "floor" && (
        <FloorStep
          onNewOrder={(table) => go("order", table, null)}
          onAddMore={(order, table) => go("order", table, order)}
          onPay={(order, table) => go("pay", table, order)}
        />
      )}
      {step === "order" && (
        <OrderStep
          tableId={tableId}
          orderId={orderId}
          onBack={() => go("floor")}
          onSent={(order, next) => (next === "pay" ? go("pay", tableId, order) : go("floor"))}
        />
      )}
      {step === "pay" && orderId !== null && (
        <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
          <OrderDetail key={`detail-${orderId}`} orderId={orderId} />
          <PaymentPanel
            key={`payment-${orderId}`}
            orderId={orderId}
            onPaid={({ change: given }) => {
              setChange(given);
              go("done", tableId, orderId);
            }}
          />
        </div>
      )}
      {step === "done" && orderId !== null && (
        <DoneStep orderId={orderId} change={change} onFinish={() => go("floor")} />
      )}
    </div>
  );
}
```

Remove `onPayNow`/`payNow` leftovers from Task C2.

- [ ] **Step 5: Wrap the page in Suspense** (`app/(app)/sales/page.tsx`)

```tsx
import { Suspense } from "react";

import { LoadingState } from "@/components/page-states";
import { SalesWorkspace } from "@/features/sales/sales-workspace";

export default function SalesPage() {
  return (
    <Suspense fallback={<LoadingState rows={6} />}>
      <SalesWorkspace />
    </Suspense>
  );
}
```

- [ ] **Step 6: Delete the old lookup** — `git rm apps/web/src/features/sales/order-lookup.tsx apps/web/src/features/sales/order-lookup.test.tsx` (read both first; confirm nothing else imports `OrderLookup` with `grep -rn "order-lookup" apps/web/src`).

- [ ] **Step 7: Run everything for the web**

Run: `cd apps/web && pnpm vitest run && pnpm lint && pnpm typecheck && pnpm build`
Expected: all PASS; `/sales` still listed as prerendered (○).

- [ ] **Step 8: Commit**

```bash
git add -A apps/web/src/features/sales "apps/web/src/app/(app)/sales/page.tsx"
git commit -m "feat(sales): split the sales screen into floor, order and payment steps"
```

---

## Phase D — Assistant API

### Task D1: Structured answer parsing and composition

**Files:**
- Create: `apps/api/src/app/modules/ai/pipeline/answer_format.py`
- Test: `apps/api/tests/modules/test_ai_answer_format.py` (create)

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class StructuredAnswer: headline: str; highlights: list[str]; follow_ups: list[str]`
  - `parse_model_answer(raw: str) -> StructuredAnswer` (headline `""` only when `raw` is blank)
  - `compose_answer(answer: StructuredAnswer, scope_note: str) -> str`
  - `split_answer(text: str) -> tuple[str, list[str]]`
  - constants `SCOPE_PREFIX = "Phạm vi dữ liệu:"`, `MAX_HIGHLIGHTS = 4`, `MAX_FOLLOW_UPS = 3`

- [ ] **Step 1: Write the failing tests**

```python
"""Structured answers: parse the model's JSON, fall back to text, and round-trip the stored form."""

import json

from app.modules.ai.pipeline.answer_format import (
    StructuredAnswer,
    compose_answer,
    parse_model_answer,
    split_answer,
)

NOTE = "Phạm vi dữ liệu: vw_ai_thungan — đơn hàng, hóa đơn và thanh toán."


def test_valid_json_is_parsed():
    raw = json.dumps({"headline": "Doanh thu 7 ngày đạt 128.450.000 ₫.",
                      "highlights": ["CN cao nhất 22.100.000 ₫.", "T2 thấp nhất 12.400.000 ₫."],
                      "follow_ups": ["So với tuần trước?"]}, ensure_ascii=False)
    answer = parse_model_answer(raw)
    assert answer.headline == "Doanh thu 7 ngày đạt 128.450.000 ₫."
    assert answer.highlights == ["CN cao nhất 22.100.000 ₫.", "T2 thấp nhất 12.400.000 ₫."]
    assert answer.follow_ups == ["So với tuần trước?"]


def test_a_code_fence_is_stripped():
    raw = '```json\n{"headline": "Có 42 đơn.", "highlights": [], "follow_ups": []}\n```'
    assert parse_model_answer(raw).headline == "Có 42 đơn."


def test_plain_text_falls_back_to_the_headline():
    answer = parse_model_answer("Hôm qua có 42 đơn hàng.")
    assert answer == StructuredAnswer("Hôm qua có 42 đơn hàng.", [], [])


def test_wrong_shapes_are_sanitised():
    raw = json.dumps({"headline": "  Có   5 món. ", "highlights": "không phải danh sách",
                      "follow_ups": ["A?", "a?", "", 3, "B?", "C?", "D?"]})
    answer = parse_model_answer(raw)
    assert answer.headline == "Có 5 món."
    assert answer.highlights == []
    assert answer.follow_ups == ["A?", "B?", "C?"]


def test_lists_and_lengths_are_capped():
    raw = json.dumps({"headline": "x" * 500, "highlights": [f"ý {i}" for i in range(9)],
                      "follow_ups": ["y" * 400]})
    answer = parse_model_answer(raw)
    assert len(answer.headline) == 300
    assert len(answer.highlights) == 4
    assert len(answer.follow_ups[0]) == 200


def test_json_without_a_headline_falls_back_to_text():
    raw = json.dumps({"highlights": ["a"]})
    assert parse_model_answer(raw).headline == raw


def test_blank_output_gives_an_empty_headline():
    assert parse_model_answer("   ").headline == ""


def test_compose_then_split_round_trips():
    answer = StructuredAnswer("Có 42 đơn.", ["30 tại chỗ.", "12 mang về."], ["?"])
    text = compose_answer(answer, NOTE)
    assert text == "Có 42 đơn.\n- 30 tại chỗ.\n- 12 mang về.\n\n" + NOTE
    assert split_answer(text) == ("Có 42 đơn.", ["30 tại chỗ.", "12 mang về."])


def test_an_old_free_form_record_splits_into_a_headline():
    old = "Hôm qua có 42 đơn hàng, nhiều hơn hôm kia.\n\n" + NOTE
    assert split_answer(old) == ("Hôm qua có 42 đơn hàng, nhiều hơn hôm kia.", [])
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_ai_answer_format.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `answer_format.py`**

```python
"""Structured assistant answers.

The interpreter asks the model for JSON; this module turns whatever comes back into a
bounded `StructuredAnswer`, and converts it to and from the plain text stored in
`TRUY_VAN_AI.KetQuaTomTat`. Nothing here trusts the model's output shape.
"""

import json
import re
from dataclasses import dataclass, field
from typing import Any

SCOPE_PREFIX = "Phạm vi dữ liệu:"
MAX_HEADLINE = 300
MAX_HIGHLIGHT = 300
MAX_HIGHLIGHTS = 4
MAX_FOLLOW_UP = 200
MAX_FOLLOW_UPS = 3

_FENCE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


@dataclass(frozen=True)
class StructuredAnswer:
    headline: str
    highlights: list[str] = field(default_factory=list)
    follow_ups: list[str] = field(default_factory=list)


def _clip(value: str, limit: int) -> str:
    text = " ".join(value.split())
    return text if len(text) <= limit else text[:limit]


def _strings(value: Any, limit: int, cap: int) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: set[str] = set()
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = _clip(item, limit)
        key = text.casefold()
        if not text or key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) == cap:
            break
    return out


def parse_model_answer(raw: str) -> StructuredAnswer:
    text = _FENCE.sub("", raw.strip()).strip()
    try:
        data = json.loads(text)
    except ValueError:
        data = None
    if isinstance(data, dict) and isinstance(data.get("headline"), str):
        headline = _clip(data["headline"], MAX_HEADLINE)
        if headline:
            return StructuredAnswer(
                headline=headline,
                highlights=_strings(data.get("highlights"), MAX_HIGHLIGHT, MAX_HIGHLIGHTS),
                follow_ups=_strings(data.get("follow_ups"), MAX_FOLLOW_UP, MAX_FOLLOW_UPS),
            )
    return StructuredAnswer(headline=raw.strip())


def compose_answer(answer: StructuredAnswer, scope_note: str) -> str:
    lines = [answer.headline, *(f"- {point}" for point in answer.highlights)]
    return "\n".join(lines) + f"\n\n{scope_note}"


def split_answer(text: str) -> tuple[str, list[str]]:
    paragraphs = text.strip().split("\n\n")
    if len(paragraphs) > 1 and paragraphs[-1].startswith(SCOPE_PREFIX):
        paragraphs = paragraphs[:-1]
    body = "\n\n".join(paragraphs).strip()
    lines = body.split("\n")
    bullets = [line[2:].strip() for line in lines if line.startswith("- ")]
    if not bullets:
        return body, []
    head = " ".join(line.strip() for line in lines if not line.startswith("- ")).strip()
    return head, bullets
```

- [ ] **Step 4: Run, lint, type-check, commit**

```bash
cd apps/api && uv run pytest tests/modules/test_ai_answer_format.py -q && uv run ruff check src/app/modules/ai tests/modules/test_ai_answer_format.py && uv run mypy src
git add apps/api/src/app/modules/ai/pipeline/answer_format.py apps/api/tests/modules/test_ai_answer_format.py
git commit -m "feat(ai): parse structured answers from the model with a plain-text fallback"
```

### Task D2: Column labels and kinds

**Files:**
- Create: `apps/api/src/app/modules/ai/labels.py`
- Test: `apps/api/tests/modules/test_ai_labels.py` (create)

**Interfaces:**
- Produces: `Kind = Literal["text", "money", "number", "date", "datetime", "percent"]`; `def describe_columns(columns: list[str], rows: list[dict[str, Any]]) -> list[dict[str, str]]` returning `[{"key", "label", "kind"}]` in column order.

- [ ] **Step 1: Write the failing tests**

```python
from app.modules.ai.labels import describe_columns


def _one(column, rows):
    return describe_columns([column], rows)[0]


def test_known_view_columns_get_vietnamese_labels_and_kinds():
    cols = describe_columns(["TenMon", "TongTien", "BusinessDate", "SoLuong"],
                            [{"TenMon": "Phở", "TongTien": "65000.0000", "BusinessDate": "2026-09-26", "SoLuong": 2}])
    assert cols == [
        {"key": "TenMon", "label": "Tên món", "kind": "text"},
        {"key": "TongTien", "label": "Tổng tiền", "kind": "money"},
        {"key": "BusinessDate", "label": "Ngày kinh doanh", "kind": "date"},
        {"key": "SoLuong", "label": "Số lượng", "kind": "number"},
    ]


def test_common_aliases_are_known():
    assert _one("DoanhThu", [{"DoanhThu": 1}]) == {"key": "DoanhThu", "label": "Doanh thu", "kind": "money"}
    assert _one("SoDon", [{"SoDon": 3}])["label"] == "Số đơn"


def test_unknown_names_are_guessed_from_the_name():
    assert _one("TongTienThang", [{"TongTienThang": 5}])["kind"] == "money"
    assert _one("TyLeHuy", [{"TyLeHuy": 3.5}])["kind"] == "percent"
    assert _one("NgayCuoi", [{"NgayCuoi": "2026-09-01"}])["kind"] == "date"
    assert _one("ThoiDiemMo", [{"ThoiDiemMo": "2026-09-01T10:00:00"}])["kind"] == "datetime"


def test_unknown_numeric_values_are_numbers_and_labels_split_camel_case():
    assert _one("TongSoDonMoi", [{"TongSoDonMoi": 4}]) == {
        "key": "TongSoDonMoi", "label": "Tong So Don Moi", "kind": "number"}
    assert _one("GhiChuKhac", [{"GhiChuKhac": "x"}])["kind"] == "text"
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_ai_labels.py -q`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement `labels.py`**

```python
"""Human labels and value kinds for the assistant's result columns.

Column names come from the `vw_ai_*` views or from aliases the model writes. Known
names get a Vietnamese label; anything else is split on CamelCase (no accents are
guessed) and typed from its name, then from its values.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Literal

Kind = Literal["text", "money", "number", "date", "datetime", "percent"]

KNOWN: dict[str, tuple[str, Kind]] = {
    "BusinessDate": ("Ngày kinh doanh", "date"),
    "CanhBaoTonThap": ("Cảnh báo tồn thấp", "number"),
    "DonGiaMon": ("Đơn giá món", "money"),
    "DonGiaNhap": ("Đơn giá nhập", "money"),
    "DonViTinh": ("Đơn vị tính", "text"),
    "GiaBinhQuanThang": ("Giá bình quân tháng", "money"),
    "HanSuDungLo": ("Hạn sử dụng lô", "date"),
    "LoaiBanGhi": ("Loại bản ghi", "text"),
    "LoaiDon": ("Loại đơn", "text"),
    "LoaiGiaoDich": ("Loại giao dịch", "text"),
    "LyDoHuyOrder": ("Lý do hủy", "text"),
    "MaBan": ("Mã bàn", "text"),
    "MaGiaoDich": ("Mã giao dịch", "text"),
    "MaGiaoDichKho": ("Mã giao dịch kho", "text"),
    "MaHoaDon": ("Mã hoá đơn", "text"),
    "MaLo": ("Mã lô", "text"),
    "MaNguyenLieu": ("Mã nguyên liệu", "text"),
    "MaOrder": ("Mã order", "text"),
    "MaPhieuNhap": ("Mã phiếu nhập", "text"),
    "MucTonToiThieu": ("Mức tồn tối thiểu", "number"),
    "NgayNhapLo": ("Ngày nhập lô", "datetime"),
    "PhuongThuc": ("Phương thức", "text"),
    "SoLuong": ("Số lượng", "number"),
    "SoLuongConLai": ("Số lượng còn lại", "number"),
    "SoLuongMon": ("Số lượng món", "number"),
    "SoLuongNhap": ("Số lượng nhập", "number"),
    "SoLuongTon": ("Số lượng tồn", "number"),
    "SoTien": ("Số tiền", "money"),
    "TenMon": ("Tên món", "text"),
    "TenNguyenLieu": ("Tên nguyên liệu", "text"),
    "TenNhaCungCap": ("Nhà cung cấp", "text"),
    "TenNhom": ("Nhóm món", "text"),
    "Thang": ("Tháng", "text"),
    "ThanhTienMon": ("Thành tiền", "money"),
    "ThoiDiemXuat": ("Thời điểm xuất", "datetime"),
    "TongSoLuongNhapThang": ("Tổng nhập trong tháng", "number"),
    "TongTien": ("Tổng tiền", "money"),
    "TrangThaiLo": ("Trạng thái lô", "text"),
    "TrangThaiOrder": ("Trạng thái order", "text"),
    # Aliases the model writes most often (data/eval).
    "DoanhThu": ("Doanh thu", "money"),
    "DoanhThuNgay": ("Doanh thu ngày", "money"),
    "DoanhThuLuyKe": ("Doanh thu luỹ kế", "money"),
    "DoanhThuThangTruoc": ("Doanh thu tháng trước", "money"),
    "TongThu": ("Tổng thu", "money"),
    "TongGiaTri": ("Tổng giá trị", "money"),
    "GiaTriHuy": ("Giá trị hủy", "money"),
    "TrungBinhMoiHoaDon": ("Trung bình mỗi hoá đơn", "money"),
    "TrungBinhHoaDon": ("Trung bình hoá đơn", "money"),
    "TrungBinhMoiNgay": ("Trung bình mỗi ngày", "money"),
    "BienLoiNhuan": ("Biên lợi nhuận", "percent"),
    "PhanTramThayDoi": ("Thay đổi (%)", "percent"),
    "TiLePhanTram": ("Tỉ lệ (%)", "percent"),
    "SoDon": ("Số đơn", "number"),
    "SoDonHuy": ("Số đơn hủy", "number"),
    "SoDonMangVe": ("Số đơn mang về", "number"),
    "SoDonDangMo": ("Số đơn đang mở", "number"),
    "SoHoaDon": ("Số hoá đơn", "number"),
    "SoGiaoDich": ("Số giao dịch", "number"),
    "SoGiaoDichTienMat": ("Giao dịch tiền mặt", "number"),
    "SoGiaoDichQR": ("Giao dịch QR", "number"),
    "SoLuongBan": ("Số lượng bán", "number"),
    "SoLuongTieuHao": ("Số lượng tiêu hao", "number"),
    "SoNguyenLieu": ("Số nguyên liệu", "number"),
    "SoNguyenLieuHet": ("Nguyên liệu đã hết", "number"),
    "SoNguyenLieuCanhBao": ("Nguyên liệu cảnh báo", "number"),
    "TongNhap": ("Tổng nhập", "number"),
    "TongXuat": ("Tổng xuất", "number"),
    "TongTon": ("Tổng tồn", "number"),
    "TongTieuHao": ("Tổng tiêu hao", "number"),
    "Gio": ("Giờ", "text"),
    "SoBan": ("Số bàn", "number"),
    "SoNgay": ("Số ngày", "number"),
}

_MONEY = ("tien", "gia", "doanhthu", "loinhuan", "chiphi", "giavon", "thu")
_PERCENT = ("tyle", "tile", "phantram", "tytrong", "percent")
_DATETIME = ("thoidiem",)
_DATE = ("ngay", "date", "hansudung")
_CAMEL = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _is_number(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        Decimal(str(value))
    except InvalidOperation:
        return False
    return True


def _guess(column: str, rows: list[dict[str, Any]]) -> Kind:
    name = column.lower()
    values = [row.get(column) for row in rows if row.get(column) is not None]
    numeric = bool(values) and all(_is_number(v) for v in values)
    if any(h in name for h in _PERCENT) and numeric:
        return "percent"
    if any(h in name for h in _DATETIME):
        return "datetime"
    if any(h in name for h in _DATE):
        return "date"
    if numeric and any(h in name for h in _MONEY):
        return "money"
    return "number" if numeric else "text"


def describe_columns(columns: list[str], rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    out = []
    for column in columns:
        label, kind = KNOWN.get(column, (_CAMEL.sub(" ", column), _guess(column, rows)))
        out.append({"key": column, "label": label, "kind": kind})
    return out
```

Note: `"TongSoDonMoi"` must resolve to `number` — its name contains no money hint (`"thu"` is not in `tongsodonmoi`). `"SoDon"` hits `KNOWN` first.

- [ ] **Step 4: Run, lint, type-check, commit**

```bash
cd apps/api && uv run pytest tests/modules/test_ai_labels.py -q && uv run ruff check src/app/modules/ai tests/modules/test_ai_labels.py && uv run mypy src
git add apps/api/src/app/modules/ai/labels.py apps/api/tests/modules/test_ai_labels.py
git commit -m "feat(ai): label result columns in Vietnamese with a value kind"
```

### Task D3: Structured `/assistant/chat` response

**Files:**
- Modify: `apps/api/src/app/modules/ai/pipeline/interpreter.py`, `apps/api/src/app/modules/ai/schemas.py`, `apps/api/src/app/modules/ai/service.py`
- Test: `apps/api/tests/modules/test_ai_interpreter.py` (update two tests), `apps/api/tests/modules/test_ai_service.py` (append)

**Interfaces:**
- Consumes: D1 `StructuredAnswer`, `parse_model_answer`, `compose_answer`; D2 `describe_columns`.
- Produces:
  - `@dataclass(frozen=True) class Interpretation: answer: StructuredAnswer; text: str; scope_note: str` and `async def interpret(...) -> Interpretation`
  - `ChatResponse` fields `headline: str`, `highlights: list[str]`, `follow_ups: list[str]`, `scope_note: str | None`, `columns: list[ColumnMeta]`, `kind: Literal["answer", "clarify", "refused", "error"]` (all defaulted), existing fields unchanged.

- [ ] **Step 1: Update and add tests**

In `test_ai_interpreter.py` replace the two interpret tests with:

```python
@pytest.mark.anyio
async def test_the_answer_is_vietnamese_and_carries_the_scope_note(session, fake_llm):
    """FR-AI-07 and business rule 16."""
    fake_llm.reply('{"headline": "Hôm qua có 42 đơn hàng.", "highlights": [], "follow_ups": []}')

    result = await interpret(session, "hôm qua bao nhiêu đơn?", "SELECT 1", [{"SoDon": 42}], Role.CASHIER)

    assert result.answer.headline == "Hôm qua có 42 đơn hàng."
    assert "vw_ai_thungan" in result.scope_note
    assert result.text.endswith(result.scope_note)


@pytest.mark.anyio
async def test_the_scope_note_survives_a_model_that_ignores_the_format(session, fake_llm):
    fake_llm.reply("Có 42 đơn. Phạm vi: tất cả dữ liệu.")
    result = await interpret(session, "q", "SELECT 1", [{"SoDon": 42}], Role.CASHIER)
    assert result.answer.headline == "Có 42 đơn. Phạm vi: tất cả dữ liệu."
    assert result.text.endswith(scope_note(Role.CASHIER))


@pytest.mark.anyio
async def test_an_empty_result_is_explained_not_left_blank(session, fake_llm):
    """FR-AI-09."""
    result = await interpret(session, "hôm qua bao nhiêu đơn?", "SELECT 1", [], Role.CASHIER)
    assert "không có" in result.answer.headline.lower()
    assert fake_llm.calls == 0
```

Append to `test_ai_service.py`:

```python
@pytest.mark.anyio
async def test_a_successful_turn_returns_the_structured_fields(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    fake_llm.reply_sequence([
        "SELECT COUNT(*) AS SoDon FROM vw_ai_thungan",
        '{"headline": "Có 2 đơn.", "highlights": ["Cả hai đã thanh toán."], "follow_ups": ["Doanh thu hôm nay?"]}',
    ])

    body = (await _chat(api_client, cashier_token, "hôm nay có bao nhiêu đơn?")).json()

    assert body["kind"] == "answer"
    assert body["headline"] == "Có 2 đơn."
    assert body["highlights"] == ["Cả hai đã thanh toán."]
    assert body["follow_ups"] == ["Doanh thu hôm nay?"]
    assert "vw_ai_thungan" in body["scope_note"]
    assert body["columns"] == [{"key": "SoDon", "label": "Số đơn", "kind": "number"}]
    assert body["answer"].startswith("Có 2 đơn.\n- Cả hai đã thanh toán.")


@pytest.mark.anyio
async def test_a_refused_turn_says_so_in_kind(
    api_client, cashier_token, seed_views, fake_llm, ai_engine, session
):
    fake_llm.reply("DELETE FROM vw_ai_thungan")
    body = (await _chat(api_client, cashier_token, "xoá hết đơn")).json()
    assert body["kind"] == "refused"
    assert body["headline"] == body["answer"]
    assert body["scope_note"] is None
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_ai_interpreter.py tests/modules/test_ai_service.py -q`
Expected: FAIL — `AttributeError: 'str' object has no attribute 'answer'`, missing `kind`.

- [ ] **Step 3: Rewrite `interpreter.py`'s `interpret`**

```python
@dataclass(frozen=True)
class Interpretation:
    answer: StructuredAnswer
    text: str
    scope_note: str


PROMPT = (
    "Bạn là trợ lý dữ liệu của một nhà hàng. Chỉ dựa trên kết quả truy vấn dưới đây, "
    "trả về đúng MỘT đối tượng JSON, không kèm chữ nào khác:\n"
    '{{"headline": "một câu kết luận", "highlights": ["2 đến 4 ý, mỗi ý một câu có số liệu"], '
    '"follow_ups": ["tối đa 3 câu hỏi tiếp theo về dữ liệu"]}}\n'
    "Viết tiếng Việt. Tiền viết dạng 185.000 ₫. Ngày viết dạng dd/mm/yyyy. "
    "Không nhắc tới SQL, tên bảng hay tên cột.\n"
    "Câu hỏi: {question}\n"
    "Câu SQL đã chạy: {sql}\n"
    "Kết quả ({count} dòng, hiển thị tối đa 20): {rows}"
)


async def interpret(
    session: AsyncSession,
    question: str,
    sql: str,
    rows: list[dict[str, Any]],
    role: Role,
) -> Interpretation:
    """A structured Vietnamese answer; the scope note is always appended by code."""
    note = scope_note(role)
    if not rows:
        answer = StructuredAnswer(headline=EMPTY_ANSWER)
        return Interpretation(answer, compose_answer(answer, note), note)

    prompt = PROMPT.format(question=question, sql=sql, count=len(rows), rows=rows[:20])
    raw = await asyncio.to_thread(llm.get_client().complete, prompt) or ""
    answer = parse_model_answer(raw)
    if not answer.headline:
        answer = StructuredAnswer(headline=FALLBACK_ANSWER)
    return Interpretation(answer, compose_answer(answer, note), note)
```

Add imports `from dataclasses import dataclass` and `from app.modules.ai.pipeline.answer_format import StructuredAnswer, compose_answer, parse_model_answer`.

- [ ] **Step 4: Extend `schemas.py`**

```python
from typing import Any, Literal

ColumnKind = Literal["text", "money", "number", "date", "datetime", "percent"]
AnswerKind = Literal["answer", "clarify", "refused", "error"]


class ColumnMeta(BaseModel):
    key: str
    label: str
    kind: ColumnKind


class ChatResponse(BaseModel):
    answer: str
    headline: str = ""
    highlights: list[str] = Field(default_factory=list)
    follow_ups: list[str] = Field(default_factory=list)
    scope_note: str | None = None
    columns: list[ColumnMeta] = Field(default_factory=list)
    kind: AnswerKind = "answer"
    data: list[dict[str, Any]] = Field(default_factory=list)
    chart: dict[str, Any] | None = None
    detail: QueryDetail | None = None
    session_id: int | None = None
```

- [ ] **Step 5: Update `service.answer`**

1. Replace `answer_text = await interpreter.interpret(...)` with `interpretation = await interpreter.interpret(...)` and add `columns_meta = labels.describe_columns(columns, rows)` next to the chart choice (import `from app.modules.ai import charts, labels`).
2. In each error branch set `headline=` and `kind=` on the returned `ChatResponse`: clarification → `ChatResponse(answer=exc.message, headline=exc.message, kind="clarify", session_id=...)`; quota → `kind="refused"`; `BusinessRuleError` → `answer=REFUSED_ANSWER, headline=REFUSED_ANSWER, kind="refused"`; timeout → `answer=TIMEOUT_ANSWER, headline=TIMEOUT_ANSWER, kind="error"`.
3. The success `_record(... summary=interpretation.text ...)` and the return:

```python
    return ChatResponse(
        answer=interpretation.text,
        headline=interpretation.answer.headline,
        highlights=interpretation.answer.highlights,
        follow_ups=interpretation.answer.follow_ups,
        scope_note=interpretation.scope_note,
        columns=[ColumnMeta(**meta) for meta in columns_meta],
        kind="answer",
        data=rows,
        chart=asdict(spec) if spec is not None else None,
        detail=QueryDetail(sql=sql_text, row_count=len(rows), view=ROLE_VIEWS[role], elapsed_ms=elapsed_ms),
        session_id=chat_session.id,
    )
```

Import `ColumnMeta` from `schemas`.

- [ ] **Step 6: Run the AI suite and the eval harness tests**

Run: `cd apps/api && uv run pytest tests/modules -k "ai" tests/eval -q`
Expected: all PASS. If a harness test reads `answer` as free text, it still works (the text starts with the headline).

- [ ] **Step 7: Lint, type-check, commit**

```bash
cd apps/api && uv run ruff check src/app/modules/ai tests/modules && uv run mypy src
git add apps/api/src/app/modules/ai apps/api/tests/modules/test_ai_interpreter.py apps/api/tests/modules/test_ai_service.py
git commit -m "feat(ai): return structured answers, column labels and an answer kind"
```

### Task D4: Chat history endpoints

**Files:**
- Modify: `apps/api/src/app/modules/ai/service.py` (add `list_sessions`, `session_detail`), `apps/api/src/app/modules/ai/schemas.py`, `apps/api/src/app/modules/ai/router.py`
- Test: `apps/api/tests/modules/test_ai_history.py` (create)

**Interfaces:**
- Consumes: D1 `split_answer`.
- Produces:
  - Schemas `SessionSummary{id, title, turn_count, created_at: datetime, last_at: datetime}`, `TurnOut{id, question, headline, highlights: list[str], status, occurred_at: datetime}`, `SessionDetail{id, title, turns: list[TurnOut]}`.
  - `GET /api/v1/assistant/sessions?page=1&size=30` → `Page[SessionSummary]` (`size` ≤ 100); `GET /api/v1/assistant/sessions/{id}` → `SessionDetail`; foreign or missing → 404 `NOT_FOUND`.

- [ ] **Step 1: Write the failing tests**

```python
"""Chat history: each user sees only their own sessions (AuthZ, not just AuthN)."""

from datetime import datetime, timedelta

import pytest

from app.modules.ai.models import AssistantQuery, ChatSession

BASE = datetime(2026, 9, 24, 9, 0)


async def _session_with(session, user_id: int, questions: list[str], start: datetime) -> ChatSession:
    chat = ChatSession(user_id=user_id, created_at=start)
    session.add(chat)
    await session.flush()
    for i, question in enumerate(questions):
        session.add(AssistantQuery(
            session_id=chat.id, scope="vw_ai_thungan", question=question, sql_text=None,
            status="Thành công",
            summary=f"Trả lời {i}.\n- ý {i}\n\nPhạm vi dữ liệu: vw_ai_thungan — x.",
            latency_ms=5, occurred_at=start + timedelta(minutes=i),
        ))
    await session.flush()
    return chat


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_the_list_holds_only_my_non_empty_sessions_newest_first(api_client, cashier_token, session):
    old = await _session_with(session, 2, ["Câu cũ"], BASE)
    new = await _session_with(session, 2, ["Câu mới", "Câu tiếp"], BASE + timedelta(hours=1))
    await _session_with(session, 1, ["Của quản lý"], BASE + timedelta(hours=2))
    session.add(ChatSession(user_id=2, created_at=BASE + timedelta(hours=3)))
    await session.commit()

    body = (await api_client.get("/api/v1/assistant/sessions", headers=_auth(cashier_token))).json()

    assert [item["id"] for item in body["items"]] == [new.id, old.id]
    assert body["items"][0]["title"] == "Câu mới"
    assert body["items"][0]["turn_count"] == 2
    assert body["total"] == 2


@pytest.mark.anyio
async def test_the_list_is_paginated(api_client, cashier_token, session):
    for i in range(3):
        await _session_with(session, 2, [f"Câu {i}"], BASE + timedelta(hours=i))
    await session.commit()
    body = (await api_client.get("/api/v1/assistant/sessions?page=2&size=2", headers=_auth(cashier_token))).json()
    assert [item["title"] for item in body["items"]] == ["Câu 0"]
    assert body["total"] == 3


@pytest.mark.anyio
async def test_a_session_detail_splits_each_stored_answer(api_client, cashier_token, session):
    chat = await _session_with(session, 2, ["A?", "B?"], BASE)
    await session.commit()
    body = (await api_client.get(f"/api/v1/assistant/sessions/{chat.id}", headers=_auth(cashier_token))).json()
    assert body["title"] == "A?"
    assert [t["question"] for t in body["turns"]] == ["A?", "B?"]
    assert body["turns"][0]["headline"] == "Trả lời 0."
    assert body["turns"][0]["highlights"] == ["ý 0"]


@pytest.mark.anyio
async def test_someone_elses_session_is_not_found(api_client, cashier_token, session):
    chat = await _session_with(session, 1, ["Của quản lý"], BASE)
    await session.commit()
    resp = await api_client.get(f"/api/v1/assistant/sessions/{chat.id}", headers=_auth(cashier_token))
    missing = await api_client.get("/api/v1/assistant/sessions/999999", headers=_auth(cashier_token))
    assert resp.status_code == 404
    assert missing.status_code == 404
    assert resp.json() == missing.json()


@pytest.mark.anyio
async def test_history_needs_a_login(api_client):
    assert (await api_client.get("/api/v1/assistant/sessions")).status_code == 401
```

- [ ] **Step 2: Run to verify failure**

Run: `cd apps/api && uv run pytest tests/modules/test_ai_history.py -q`
Expected: FAIL — 404/405 on `/assistant/sessions`.

- [ ] **Step 3: Add schemas** (`schemas.py`)

```python
class SessionSummary(BaseModel):
    id: int
    title: str
    turn_count: int
    created_at: datetime
    last_at: datetime


class TurnOut(BaseModel):
    id: int
    question: str
    headline: str
    highlights: list[str]
    status: str
    occurred_at: datetime


class SessionDetail(BaseModel):
    id: int
    title: str
    turns: list[TurnOut]
```

(`from datetime import datetime`.)

- [ ] **Step 4: Add service functions** (`service.py`)

```python
TITLE_LIMIT = 120


def _title(question: str) -> str:
    text = " ".join(question.split())
    return text if len(text) <= TITLE_LIMIT else text[: TITLE_LIMIT - 1] + "…"


async def list_sessions(
    session: AsyncSession, user_id: int, page: int, size: int
) -> tuple[list[SessionSummary], int]:
    """The caller's sessions that hold at least one turn, most recent activity first."""
    stats = (
        select(
            AssistantQuery.session_id.label("sid"),
            func.count(AssistantQuery.id).label("turns"),
            func.min(AssistantQuery.id).label("first_id"),
            func.max(AssistantQuery.occurred_at).label("last_at"),
        )
        .group_by(AssistantQuery.session_id)
        .subquery()
    )
    base = (
        select(ChatSession, stats.c.turns, stats.c.first_id, stats.c.last_at)
        .join(stats, stats.c.sid == ChatSession.id)
        .where(ChatSession.user_id == user_id)
    )
    total = (await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    rows = (
        await session.execute(
            base.order_by(stats.c.last_at.desc(), ChatSession.id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).all()
    first_ids = [row.first_id for row in rows]
    questions = dict(
        (
            await session.execute(
                select(AssistantQuery.id, AssistantQuery.question).where(AssistantQuery.id.in_(first_ids))
            )
        ).all()
    ) if first_ids else {}
    items = [
        SessionSummary(
            id=row.ChatSession.id,
            title=_title(questions.get(row.first_id, "")),
            turn_count=row.turns,
            created_at=row.ChatSession.created_at,
            last_at=row.last_at,
        )
        for row in rows
    ]
    return items, total


async def session_detail(session: AsyncSession, user_id: int, session_id: int) -> SessionDetail:
    chat = await session.get(ChatSession, session_id)
    # Someone else's session answers exactly like a missing one.
    if chat is None or chat.user_id != user_id:
        raise NotFoundError("Không tìm thấy cuộc trò chuyện.")
    turns = (
        (
            await session.execute(
                select(AssistantQuery)
                .where(AssistantQuery.session_id == chat.id)
                .order_by(AssistantQuery.occurred_at, AssistantQuery.id)
            )
        )
        .scalars()
        .all()
    )
    out = []
    for turn in turns:
        headline, highlights = split_answer(turn.summary or "")
        out.append(
            TurnOut(
                id=turn.id,
                question=turn.question,
                headline=headline,
                highlights=highlights,
                status=turn.status,
                occurred_at=turn.occurred_at,
            )
        )
    return SessionDetail(id=chat.id, title=_title(turns[0].question) if turns else "", turns=out)
```

Imports: `from sqlalchemy import func, select`, `from app.core.errors import BusinessRuleError, NotFoundError`, `from app.modules.ai.pipeline.answer_format import split_answer`, the new schemas.

- [ ] **Step 5: Add routes** (`router.py`)

```python
@router.get("/sessions", response_model=Page[SessionSummary])
async def list_sessions(
    user: CurrentUser,
    page: int = Query(1, ge=1),
    size: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> Page[SessionSummary]:
    items, total = await service.list_sessions(session, user.user_id, page, size)
    return Page[SessionSummary](items=items, total=total, page=page, size=size)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: int, user: CurrentUser, session: AsyncSession = Depends(get_session)
) -> SessionDetail:
    return await service.session_detail(session, user.user_id, session_id)
```

Imports: `Query`, `from app.shared.pagination import Page`, the two schemas. Update the module docstring: "`POST /assistant/chat` answers one turn; `GET /assistant/sessions[/{id}]` reads the caller's own history."

- [ ] **Step 6: Run, lint, type-check, commit**

```bash
cd apps/api && uv run pytest tests/modules/test_ai_history.py tests/modules -k ai -q && uv run ruff check src/app/modules/ai tests/modules/test_ai_history.py && uv run mypy src
git add apps/api/src/app/modules/ai apps/api/tests/modules/test_ai_history.py
git commit -m "feat(ai): let each user list and reopen their own chat sessions"
```

---

## Phase E — Assistant web

### Task E1: Types, cell formatting and labelled charts

**Files:**
- Modify: `apps/web/src/types/api.ts`, `apps/web/src/features/assistant/chart-view.tsx`
- Create: `apps/web/src/features/assistant/format-cell.ts`, `apps/web/src/features/assistant/suggestions.ts`
- Test: `apps/web/src/features/assistant/format-cell.test.ts` (create)

**Interfaces:**
- Produces:
  - types `ColumnKind`, `ColumnMeta`, `AnswerKind`, extended `ChatResponse`, `SessionSummary`, `TurnOut`, `SessionDetail` (mirror D3/D4 exactly)
  - `formatCell(value: unknown, kind: ColumnKind): string`, `isNumericKind(kind: ColumnKind): boolean`, `columnsFor(rows: Record<string, unknown>[], columns?: ColumnMeta[]): ColumnMeta[]`
  - `ChartView({ spec, rows, columns? })`
  - `type Suggestion = { topic: string; module: ModuleKey; text: string }`, `suggestionsFor(role: string | undefined, module?: ModuleKey): Suggestion[]`

- [ ] **Step 1: Write the failing test** (`format-cell.test.ts`)

```ts
import { describe, expect, it } from "vitest";

import { columnsFor, formatCell, isNumericKind } from "./format-cell";
import { suggestionsFor } from "./suggestions";

describe("formatCell", () => {
  it("formats each kind", () => {
    expect(formatCell("65000.0000", "money")).toBe("65.000 ₫");
    expect(formatCell(1234.5, "number")).toBe("1.234,5");
    expect(formatCell("12.5", "percent")).toBe("12,5%");
    expect(formatCell("2026-09-26", "date")).toBe("26/09/2026");
    expect(formatCell(null, "money")).toBe("");
    expect(formatCell("Phở bò", "text")).toBe("Phở bò");
  });

  it("keeps a non-numeric value readable under a numeric kind", () => {
    expect(formatCell("n/a", "number")).toBe("n/a");
  });

  it("falls back to raw keys when the API sent no column metadata", () => {
    expect(columnsFor([{ A: 1 }])).toEqual([{ key: "A", label: "A", kind: "text" }]);
    expect(columnsFor([])).toEqual([]);
  });

  it("knows which kinds are right-aligned", () => {
    expect(isNumericKind("money")).toBe(true);
    expect(isNumericKind("date")).toBe(false);
  });
});

describe("suggestionsFor", () => {
  it("filters by role and by module", () => {
    expect(suggestionsFor("WAREHOUSE").every((s) => s.module === "inventory")).toBe(true);
    expect(suggestionsFor("MANAGER", "inventory").length).toBeGreaterThan(0);
    expect(suggestionsFor("MANAGER", "inventory").every((s) => s.module === "inventory")).toBe(true);
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd apps/web && pnpm vitest run src/features/assistant/format-cell.test.ts` → FAIL (module not found).

- [ ] **Step 3: Extend `types/api.ts`** (replace `ChatResponse`, append the rest)

```ts
export type ColumnKind = "text" | "money" | "number" | "date" | "datetime" | "percent";

export interface ColumnMeta {
  key: string;
  label: string;
  kind: ColumnKind;
}

export type AnswerKind = "answer" | "clarify" | "refused" | "error";

export interface ChatResponse {
  answer: string;
  headline: string;
  highlights: string[];
  follow_ups: string[];
  scope_note: string | null;
  columns: ColumnMeta[];
  kind: AnswerKind;
  data: Record<string, unknown>[];
  chart: ChartSpec | null;
  detail: QueryDetail | null;
  session_id?: number | null;
}

export interface SessionSummary {
  id: number;
  title: string;
  turn_count: number;
  created_at: string;
  last_at: string;
}

export interface TurnOut {
  id: number;
  question: string;
  headline: string;
  highlights: string[];
  status: string;
  occurred_at: string;
}

export interface SessionDetail {
  id: number;
  title: string;
  turns: TurnOut[];
}
```

- [ ] **Step 4: Create `format-cell.ts`**

```ts
import { formatDate, formatDateTime, formatNumber, formatVnd } from "@/lib/format";
import type { ColumnKind, ColumnMeta } from "@/types/api";

export function isNumericKind(kind: ColumnKind): boolean {
  return kind === "money" || kind === "number" || kind === "percent";
}

export function formatCell(value: unknown, kind: ColumnKind): string {
  if (value === null || value === undefined || value === "") return "";
  const raw = String(value);
  switch (kind) {
    case "money":
      return formatVnd(raw) || raw;
    case "number":
      return formatNumber(raw) || raw;
    case "percent": {
      const text = formatNumber(raw);
      return text ? `${text}%` : raw;
    }
    case "date":
      return formatDate(raw);
    case "datetime":
      return formatDateTime(raw);
    default:
      return raw;
  }
}

export function columnsFor(rows: Record<string, unknown>[], columns?: ColumnMeta[]): ColumnMeta[] {
  if (columns && columns.length > 0) return columns;
  return rows.length > 0 ? Object.keys(rows[0]).map((key) => ({ key, label: key, kind: "text" })) : [];
}
```

- [ ] **Step 5: Create `suggestions.ts`** (moves the list out of `chat-panel.tsx`)

```ts
import type { ModuleKey } from "@/lib/modules";

export type Suggestion = { topic: string; module: ModuleKey; text: string };

const BY_ROLE: Record<string, Suggestion[]> = {
  MANAGER: [
    { topic: "Doanh thu", module: "reports", text: "Doanh thu 7 ngày gần nhất theo từng ngày?" },
    { topic: "Món ăn", module: "catalog", text: "Món nào bán chạy nhất tuần này?" },
    { topic: "Thanh toán", module: "sales", text: "So sánh doanh thu tiền mặt và QR tháng này" },
    { topic: "Kho", module: "inventory", text: "Nguyên liệu nào đang dưới mức tối thiểu?" },
    { topic: "Kho", module: "inventory", text: "Những lô nào sắp hết hạn trong tuần này?" },
    { topic: "Báo cáo", module: "reports", text: "Tỉ lệ order bị hủy tháng này là bao nhiêu?" },
    { topic: "Cài đặt", module: "settings", text: "Hôm nay có bao nhiêu hoá đơn đã thanh toán?" },
  ],
  CASHIER: [
    { topic: "Hoá đơn", module: "sales", text: "Hôm nay đã có bao nhiêu hóa đơn?" },
    { topic: "Doanh thu", module: "sales", text: "Doanh thu ca hôm nay là bao nhiêu?" },
    { topic: "Đối soát", module: "sales", text: "Có order nào đang chờ đối soát không?" },
    { topic: "Món ăn", module: "catalog", text: "Món nào bán chạy nhất hôm nay?" },
  ],
  WAREHOUSE: [
    { topic: "Tồn kho", module: "inventory", text: "Nguyên liệu nào đang dưới mức tối thiểu?" },
    { topic: "Tồn kho", module: "inventory", text: "Tồn kho thịt bò hiện còn bao nhiêu?" },
    { topic: "Lô hàng", module: "inventory", text: "Những lô nào sắp hết hạn trong tuần này?" },
  ],
};

export function suggestionsFor(role: string | undefined, module?: ModuleKey): Suggestion[] {
  const all = BY_ROLE[role ?? ""] ?? BY_ROLE.MANAGER;
  if (!module) return all;
  const matching = all.filter((s) => s.module === module);
  return matching.length > 0 ? matching : all;
}
```

- [ ] **Step 6: Label the chart** (`chart-view.tsx`)

Add `columns?: ColumnMeta[]` to the props (import `ColumnMeta` and `columnsFor`, `formatCell`). At the top of the body: `const meta = columnsFor(rows, columns); const kindOf = (key: string) => meta.find((c) => c.key === key)?.kind ?? "text";`. Change `labelOf` calls to `formatCell(row[spec.x], kindOf(spec.x))`; in the doughnut legend replace `formatNumber(series[index])` with `formatCell(series[index], kindOf(spec.y[0]))`; inside each bar `<rect>` and at each line point add `<title>{`${formatCell(rows[index][spec.x], kindOf(spec.x))}: ${formatCell(value, kindOf(spec.y[0]))}`}</title>`; change `rx={3}` to `rx={2}`. Remove the `formatNumber` import if unused.

- [ ] **Step 7: Run, lint, type-check, commit**

```bash
cd apps/web && pnpm vitest run src/features/assistant && pnpm lint && pnpm typecheck
git add apps/web/src/types/api.ts apps/web/src/features/assistant
git commit -m "feat(assistant): add column-aware formatting, labelled charts and suggestions"
```

(`chat-panel.test.tsx` may still reference the old `ChatResponse` shape; fix its fixtures by adding `headline`, `highlights: []`, `follow_ups: []`, `scope_note: null`, `columns: []`, `kind: "answer"` so typecheck passes until Task E3 deletes it.)

### Task E2: Conversation hook, composer and message rendering

**Files:**
- Create: `apps/web/src/features/assistant/use-conversation.ts`, `composer.tsx`, `result-tabs.tsx`, `assistant-message.tsx`
- Test: `apps/web/src/features/assistant/assistant-message.test.tsx`, `apps/web/src/features/assistant/use-conversation.test.tsx` (create)

**Interfaces:**
- Consumes: E1 types, `formatCell`, `columnsFor`, `isNumericKind`, `ChartView`.
- Produces:
  - `type Turn = { id: string; question: string; status: "pending" | "done" | "failed"; result: ChatResponse | null; error: string | null; restored: TurnOut | null }`
  - `useConversation(options?: { onSessionCreated?: (id: number) => void }) → { turns: Turn[]; sessionId: number | null; pending: boolean; ask(text: string): Promise<void>; reset(): void; load(detail: SessionDetail): void }`
  - `Composer({ onSubmit(text: string): void; disabled: boolean; placeholder: string; size?: "lg" | "sm"; autoFocus?: boolean })`
  - `ResultTabs({ result: ChatResponse })`
  - `AssistantMessage({ turn: Turn; compact?: boolean; onAsk(text: string): void })`

- [ ] **Step 1: Write the failing tests**

`use-conversation.test.tsx`:

```tsx
import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { useConversation } from "./use-conversation";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;
const reply = { answer: "a", headline: "Có 2 đơn.", highlights: [], follow_ups: [], scope_note: null,
  columns: [], kind: "answer", data: [], chart: null, detail: null, session_id: 9 };

describe("useConversation", () => {
  beforeEach(() => vi.resetAllMocks());

  it("sends the session id after the first turn and reports a new session once", async () => {
    fetchMock.mockResolvedValue(reply);
    const onSessionCreated = vi.fn();
    const { result } = renderHook(() => useConversation({ onSessionCreated }));

    await act(() => result.current.ask("Câu 1"));
    await act(() => result.current.ask("Câu 2"));

    expect(fetchMock.mock.calls[0][1].body).toEqual({ question: "Câu 1" });
    expect(fetchMock.mock.calls[1][1].body).toEqual({ question: "Câu 2", session_id: 9 });
    expect(onSessionCreated).toHaveBeenCalledTimes(1);
    expect(result.current.turns.map((t) => t.status)).toEqual(["done", "done"]);
  });

  it("marks a failed turn with the API message and ignores blank questions", async () => {
    fetchMock.mockRejectedValue(new ApiError(500, "X", "Máy chủ lỗi."));
    const { result } = renderHook(() => useConversation());
    await act(() => result.current.ask("   "));
    expect(fetchMock).not.toHaveBeenCalled();
    await act(() => result.current.ask("Câu"));
    expect(result.current.turns[0]).toMatchObject({ status: "failed", error: "Máy chủ lỗi." });
  });

  it("loads a stored session and continues it", async () => {
    fetchMock.mockResolvedValue(reply);
    const { result } = renderHook(() => useConversation());
    act(() => result.current.load({ id: 5, title: "Cũ", turns: [
      { id: 1, question: "Cũ?", headline: "Đáp.", highlights: [], status: "Thành công", occurred_at: "2026-09-25T10:00:00" }] }));
    expect(result.current.turns[0].restored?.headline).toBe("Đáp.");
    await act(() => result.current.ask("Tiếp?"));
    expect(fetchMock.mock.calls[0][1].body).toEqual({ question: "Tiếp?", session_id: 5 });
  });
});
```

`assistant-message.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AssistantMessage } from "./assistant-message";
import type { Turn } from "./use-conversation";

const base = { answer: "x", headline: "Doanh thu 7 ngày đạt 128.450.000 ₫.",
  highlights: ["Chủ nhật cao nhất."], follow_ups: ["So với tuần trước?"],
  scope_note: "Phạm vi dữ liệu: vw_ai_quanly — toàn bộ.", kind: "answer" as const,
  columns: [{ key: "BusinessDate", label: "Ngày kinh doanh", kind: "date" as const },
            { key: "DoanhThu", label: "Doanh thu", kind: "money" as const }],
  data: [{ BusinessDate: "2026-09-20", DoanhThu: "22100000" }],
  chart: null, detail: { sql: "SELECT 1", row_count: 1, view: "vw_ai_quanly", elapsed_ms: 840 } };

function turn(overrides: Partial<Turn> = {}): Turn {
  return { id: "1", question: "Doanh thu?", status: "done", result: base, error: null, restored: null, ...overrides };
}

describe("AssistantMessage", () => {
  it("renders the headline, highlights, labelled table and scope note", () => {
    render(<AssistantMessage turn={turn()} onAsk={vi.fn()} />);
    expect(screen.getByText(base.headline)).toBeInTheDocument();
    expect(screen.getByText("Chủ nhật cao nhất.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("tab", { name: /Bảng/ }));
    expect(screen.getByRole("columnheader", { name: "Doanh thu" })).toBeInTheDocument();
    expect(screen.getByText("22.100.000 ₫")).toBeInTheDocument();
    expect(screen.getByText("20/09/2026")).toBeInTheDocument();
    expect(screen.getByText(/vw_ai_quanly/)).toBeInTheDocument();
  });

  it("only shows tabs that have content", () => {
    render(<AssistantMessage turn={turn()} onAsk={vi.fn()} />);
    expect(screen.queryByRole("tab", { name: /Biểu đồ/ })).not.toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /SQL/ })).toBeInTheDocument();
  });

  it("asks a follow-up immediately", () => {
    const onAsk = vi.fn();
    render(<AssistantMessage turn={turn()} onAsk={onAsk} />);
    fireEvent.click(screen.getByRole("button", { name: "So với tuần trước?" }));
    expect(onAsk).toHaveBeenCalledWith("So với tuần trước?");
  });

  it("shows a clarification without a result block", () => {
    render(<AssistantMessage turn={turn({ result: { ...base, kind: "clarify", headline: "Bạn muốn xem ngày nào?", data: [], detail: null } })} onAsk={vi.fn()} />);
    expect(screen.getByText("Bạn muốn xem ngày nào?")).toBeInTheDocument();
    expect(screen.queryByRole("tablist")).not.toBeInTheDocument();
  });

  it("offers a retry on failure and a re-run for a restored turn", () => {
    const onAsk = vi.fn();
    const { rerender } = render(<AssistantMessage turn={turn({ status: "failed", result: null, error: "Mất kết nối." })} onAsk={onAsk} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Mất kết nối.");
    fireEvent.click(screen.getByRole("button", { name: "Thử lại" }));
    rerender(<AssistantMessage turn={turn({ result: null, restored: { id: 1, question: "Doanh thu?", headline: "Cũ.", highlights: [], status: "Thành công", occurred_at: "" } })} onAsk={onAsk} />);
    fireEvent.click(screen.getByRole("button", { name: "Chạy lại" }));
    expect(onAsk).toHaveBeenCalledTimes(2);
    expect(onAsk).toHaveBeenLastCalledWith("Doanh thu?");
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd apps/web && pnpm vitest run src/features/assistant` → FAIL (modules missing).

- [ ] **Step 3: Create `use-conversation.ts`**

```ts
"use client";

import { useCallback, useRef, useState } from "react";

import { ApiError, apiFetch } from "@/lib/api-client";
import type { ChatResponse, SessionDetail, TurnOut } from "@/types/api";

export type Turn = {
  id: string;
  question: string;
  status: "pending" | "done" | "failed";
  result: ChatResponse | null;
  error: string | null;
  restored: TurnOut | null;
};

export function useConversation(options: { onSessionCreated?: (id: number) => void } = {}) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [sessionId, setSessionId] = useState<number | null>(null);
  // Refs keep `ask` stable and let two quick questions see the same session id.
  const sessionRef = useRef<number | null>(null);
  const counter = useRef(0);
  const onCreated = useRef(options.onSessionCreated);
  onCreated.current = options.onSessionCreated;
  const pending = turns.some((t) => t.status === "pending");

  const ask = useCallback(async (text: string) => {
    const question = text.trim();
    if (!question) return;
    const id = `t${counter.current++}`;
    setTurns((prev) => [...prev, { id, question, status: "pending", result: null, error: null, restored: null }]);
    try {
      const current = sessionRef.current;
      const result = await apiFetch<ChatResponse>("/assistant/chat", {
        method: "POST",
        body: current === null ? { question } : { question, session_id: current },
      });
      if (current === null && result.session_id != null) {
        sessionRef.current = result.session_id;
        setSessionId(result.session_id);
        onCreated.current?.(result.session_id);
      }
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: "done", result } : t)));
    } catch (cause) {
      const error = cause instanceof ApiError ? cause.message : "Không kết nối được máy chủ API.";
      setTurns((prev) => prev.map((t) => (t.id === id ? { ...t, status: "failed", error } : t)));
    }
  }, []);

  const reset = useCallback(() => {
    sessionRef.current = null;
    setSessionId(null);
    setTurns([]);
  }, []);

  const load = useCallback((detail: SessionDetail) => {
    sessionRef.current = detail.id;
    setSessionId(detail.id);
    setTurns(
      detail.turns.map((t) => ({
        id: `h${t.id}`,
        question: t.question,
        status: "done",
        result: null,
        error: null,
        restored: t,
      })),
    );
  }, []);

  return { turns, sessionId, pending, ask, reset, load };
}
```

- [ ] **Step 4: Create `composer.tsx`**

```tsx
"use client";

import { ArrowUp } from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

const LIMIT = 500;

export function Composer({
  onSubmit,
  disabled,
  placeholder,
  size = "lg",
  autoFocus = false,
  children,
}: {
  onSubmit: (text: string) => void;
  disabled: boolean;
  placeholder: string;
  size?: "lg" | "sm";
  autoFocus?: boolean;
  children?: React.ReactNode;
}) {
  const [text, setText] = useState("");
  const area = useRef<HTMLTextAreaElement>(null);

  useLayoutEffect(() => {
    const el = area.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }, [text]);

  function submit() {
    if (disabled || !text.trim()) return;
    onSubmit(text);
    setText("");
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        submit();
      }}
      className={cn(
        "grid gap-2 border border-border-strong bg-surface shadow-float focus-within:border-ink focus-within:ring-1 focus-within:ring-ink",
        size === "lg" ? "rounded-overlay px-3.5 pt-3 pb-2" : "rounded-container px-3 pt-2 pb-1.5",
      )}
    >
      <label htmlFor={`composer-${size}`} className="sr-only">
        Câu hỏi bằng tiếng Việt
      </label>
      <textarea
        id={`composer-${size}`}
        ref={area}
        rows={1}
        autoFocus={autoFocus}
        maxLength={LIMIT}
        value={text}
        placeholder={placeholder}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
            e.preventDefault();
            submit();
          }
        }}
        className={cn(
          "w-full resize-none bg-transparent outline-none placeholder:text-subtle",
          size === "lg" ? "min-h-11 text-[15px] leading-[22px]" : "min-h-6 text-sm",
        )}
      />
      <div className="flex items-center gap-2">
        {children}
        <span className="ml-auto text-xs text-subtle tabular-nums">
          {text.length}/{LIMIT}
        </span>
        <button
          type="submit"
          aria-label="Gửi câu hỏi"
          disabled={disabled || !text.trim()}
          className="grid size-9 place-items-center rounded-control bg-primary text-white hover:bg-primary-hover disabled:opacity-40"
        >
          <ArrowUp className="size-4" aria-hidden />
        </button>
      </div>
    </form>
  );
}
```

- [ ] **Step 5: Create `result-tabs.tsx`**

```tsx
"use client";

import { ChartColumn, CodeXml, ShieldCheck, Table2 } from "lucide-react";
import { useState } from "react";

import { DataPagination } from "@/components/data-pagination";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useClientPagination } from "@/lib/use-client-pagination";
import { cn } from "@/lib/utils";
import type { ChatResponse } from "@/types/api";

import { ChartView } from "./chart-view";
import { columnsFor, formatCell, isNumericKind } from "./format-cell";

type Tab = "chart" | "table" | "sql";

function ResultTable({ result }: { result: ChatResponse }) {
  const paging = useClientPagination(result.data, "", 10);
  const columns = columnsFor(result.data, result.columns);
  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((c) => (
              <TableHead key={c.key} className={cn(isNumericKind(c.kind) && "text-right")}>
                {c.label}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {paging.pageItems.map((row, index) => (
            <TableRow key={index}>
              {columns.map((c) => (
                <TableCell key={c.key} className={cn(isNumericKind(c.kind) && "text-right tabular-nums")}>
                  {formatCell(row[c.key], c.kind)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {result.data.length > paging.pageSize && (
        <DataPagination page={paging.page} pageSize={paging.pageSize} total={paging.total} onPageChange={paging.setPage} />
      )}
    </div>
  );
}

export function ResultTabs({ result }: { result: ChatResponse }) {
  const tabs: { key: Tab; label: string; Icon: typeof ChartColumn }[] = [];
  if (result.chart && result.data.length > 0) tabs.push({ key: "chart", label: "Biểu đồ", Icon: ChartColumn });
  if (result.data.length > 0) tabs.push({ key: "table", label: "Bảng", Icon: Table2 });
  if (result.detail) tabs.push({ key: "sql", label: "SQL", Icon: CodeXml });
  const [active, setActive] = useState<Tab | null>(tabs[0]?.key ?? null);
  if (tabs.length === 0 || active === null) return null;

  return (
    <div className="overflow-hidden rounded-container border border-border bg-surface">
      <div role="tablist" aria-label="Kết quả" className="flex items-center gap-0.5 border-b border-border pr-3 pl-1">
        {tabs.map(({ key, label, Icon }) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={active === key}
            onClick={() => setActive(key)}
            className={cn(
              "inline-flex items-center gap-1.5 px-2.5 py-2.5 font-semibold text-muted shadow-[inset_0_-2px_0_0_transparent]",
              active === key && "text-ink shadow-[inset_0_-2px_0_0_var(--color-ink)]",
            )}
          >
            <Icon className="size-4" aria-hidden />
            {label}
          </button>
        ))}
        {result.detail && (
          <span className="ml-auto text-xs whitespace-nowrap text-subtle tabular-nums">
            {result.detail.row_count} dòng · {(result.detail.elapsed_ms / 1000).toLocaleString("vi-VN", { maximumFractionDigits: 2 })} giây
          </span>
        )}
      </div>
      <div role="tabpanel" className={cn(active !== "table" && "p-3.5")}>
        {active === "chart" && <ChartView spec={result.chart} rows={result.data} columns={result.columns} />}
        {active === "table" && <ResultTable result={result} />}
        {active === "sql" && result.detail && (
          <div className="space-y-3">
            <pre className="overflow-x-auto font-mono text-xs leading-5 whitespace-pre-wrap">{result.detail.sql}</pre>
            <p className="flex items-center gap-2 rounded-control bg-success-subtle px-2.5 py-2 text-[13px] font-semibold text-success-fg">
              <ShieldCheck className="size-4 shrink-0" aria-hidden />
              Đã qua kiểm duyệt: chỉ đọc, đúng view {result.detail.view} của vai trò, có giới hạn số dòng.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
```

The table tab has no padding so the `Table` border sits flush; `Table` already renders its own border — override with `className` only if a double border appears.

- [ ] **Step 6: Create `assistant-message.tsx`**

```tsx
"use client";

import { ArrowRight, CircleAlert, CircleHelp, Copy, RefreshCw, RotateCcw, ShieldCheck, UtensilsCrossed } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { ResultTabs } from "./result-tabs";
import type { Turn } from "./use-conversation";

function Elapsed() {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="tabular-nums">{seconds}</span>;
}

function Points({ headline, highlights }: { headline: string; highlights: string[] }) {
  return (
    <>
      <p className="text-base leading-[25px] font-bold text-pretty">{headline}</p>
      {highlights.length > 0 && (
        <ul className="grid gap-1.5 text-[15px] leading-[23px]">
          {highlights.map((point) => (
            <li key={point} className="grid grid-cols-[14px_minmax(0,1fr)] gap-2">
              <span aria-hidden className="mt-[9px] size-1.5 bg-ink" />
              <span>{point}</span>
            </li>
          ))}
        </ul>
      )}
    </>
  );
}

export function AssistantMessage({ turn, compact = false, onAsk }: { turn: Turn; compact?: boolean; onAsk: (text: string) => void }) {
  const result = turn.result;

  async function copy() {
    if (!result) return;
    const text = [result.headline, ...result.highlights.map((p) => `- ${p}`), "", result.scope_note ?? ""].join("\n").trim();
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Đã sao chép câu trả lời.");
    } catch {
      toast.error("Trình duyệt không cho sao chép. Hãy chọn và sao chép thủ công.");
    }
  }

  let body: React.ReactNode;
  if (turn.status === "pending") {
    body = (
      <p role="status" className="flex h-8 items-center gap-2.5 font-medium text-muted">
        <span aria-hidden className="size-2 bg-ink motion-safe:animate-pulse" />
        Đang phân tích câu hỏi · <Elapsed /> giây
      </p>
    );
  } else if (turn.status === "failed") {
    body = (
      <div role="alert" className="flex flex-wrap items-center gap-3 rounded-container bg-danger-subtle px-3.5 py-3 text-danger-fg shadow-[inset_4px_0_0_0_var(--color-danger)]">
        <CircleAlert className="size-4 shrink-0" aria-hidden />
        <p className="flex-1 font-medium">{turn.error}</p>
        <Button variant="secondary" size="sm" onClick={() => onAsk(turn.question)}>Thử lại</Button>
      </div>
    );
  } else if (turn.restored) {
    body = (
      <>
        <Points headline={turn.restored.headline} highlights={turn.restored.highlights} />
        <div className="flex flex-wrap items-center gap-2 text-[13px] text-subtle">
          Bảng và biểu đồ của lượt cũ không được lưu.
          <Button variant="ghost" size="sm" onClick={() => onAsk(turn.question)}>
            <RefreshCw />
            Chạy lại
          </Button>
        </div>
      </>
    );
  } else if (result && result.kind !== "answer") {
    const warn = result.kind === "clarify" || result.kind === "refused";
    body = (
      <div className={cn("grid gap-1.5 rounded-container border border-border bg-surface px-3.5 py-3",
        warn ? "shadow-[inset_3px_0_0_0_var(--color-warning)]" : "shadow-[inset_3px_0_0_0_var(--color-danger)]")}>
        <p className="flex items-center gap-2 font-bold">
          {warn ? <CircleHelp className="size-4 text-warning" aria-hidden /> : <CircleAlert className="size-4 text-danger" aria-hidden />}
          {result.kind === "clarify" ? "Cần làm rõ câu hỏi" : result.kind === "refused" ? "Không trả lời được câu này" : "Có lỗi khi trả lời"}
        </p>
        <p className="text-[15px] leading-[23px]">{result.headline || result.answer}</p>
      </div>
    );
  } else if (result) {
    body = (
      <>
        <Points headline={result.headline || result.answer} highlights={result.highlights} />
        <ResultTabs result={result} />
        {result.scope_note && (
          <p className="flex items-start gap-2 text-[12.5px] leading-[18px] text-subtle">
            <ShieldCheck className="mt-px size-3.5 shrink-0" aria-hidden />
            {result.scope_note} Trợ lý chỉ đọc, không sửa dữ liệu.
          </p>
        )}
        <div className="-ml-2 flex flex-wrap gap-0.5">
          <Button variant="ghost" size="sm" onClick={copy}><Copy />Sao chép</Button>
          <Button variant="ghost" size="sm" onClick={() => onAsk(turn.question)}><RotateCcw />Hỏi lại</Button>
        </div>
        {result.follow_ups.length > 0 && (
          <div className="grid gap-1.5">
            <p className="text-[11px] font-bold tracking-wider text-subtle uppercase">Hỏi tiếp</p>
            <div className="flex flex-wrap gap-1.5">
              {result.follow_ups.map((q) => (
                <button key={q} type="button" onClick={() => onAsk(q)}
                  className="inline-flex items-center gap-2 rounded-control border border-border bg-surface px-2.5 py-1.5 text-left font-medium hover:border-ink">
                  <ArrowRight className="size-3.5 text-subtle" aria-hidden />
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </>
    );
  }

  return (
    <div className="grid gap-6">
      <p className={cn("max-w-[80%] justify-self-end rounded-container border border-border bg-surface px-3.5 py-2.5", !compact && "text-[15px] leading-[22px]")}>
        {turn.question}
      </p>
      <article aria-label="Câu trả lời của trợ lý" className={cn("grid gap-3.5", !compact && "grid-cols-[32px_minmax(0,1fr)] gap-x-3.5")}>
        {!compact && (
          <span aria-hidden className="grid size-8 place-items-center rounded-control bg-ink text-white">
            <UtensilsCrossed className="size-4" />
          </span>
        )}
        <div className="grid min-w-0 gap-3.5">{body}</div>
      </article>
    </div>
  );
}
```

Note: follow-up chips' accessible name equals the question text (the icon is `aria-hidden`), which the test relies on.

- [ ] **Step 7: Run, lint, type-check, commit**

```bash
cd apps/web && pnpm vitest run src/features/assistant && pnpm lint && pnpm typecheck
git add apps/web/src/features/assistant
git commit -m "feat(assistant): render structured answers with result tabs and follow-ups"
```

### Task E3: Assistant screen with history and welcome

**Files:**
- Create: `apps/web/src/features/assistant/history-panel.tsx`, `welcome.tsx`, `assistant-screen.tsx`
- Modify: `apps/web/src/app/(app)/assistant/page.tsx`
- Delete: `apps/web/src/features/assistant/chat-panel.tsx`, `chat-panel.test.tsx` (replaced; spec §4.1) — move its `ChartView` tests into `chart-view.test.tsx` first
- Test: `apps/web/src/features/assistant/assistant-screen.test.tsx`, `history-panel.test.tsx` (create)

**Interfaces:**
- Consumes: E2 hook/components; D4 endpoints.
- Produces: `HistoryPanel({ activeId: number | null; refreshKey: number; onSelect(id: number): void; onNew(): void })`, `groupLabel(iso: string, now: Date): string`, `Welcome({ username: string | undefined; role: string | undefined; onAsk(text: string): void })`, `AssistantScreen()`.

- [ ] **Step 1: Write the failing tests**

`history-panel.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { groupLabel, HistoryPanel } from "./history-panel";

const now = new Date("2026-09-26T15:00:00");

describe("groupLabel", () => {
  it("buckets by day", () => {
    expect(groupLabel("2026-09-26T09:00:00", now)).toBe("Hôm nay");
    expect(groupLabel("2026-09-25T21:00:00", now)).toBe("Hôm qua");
    expect(groupLabel("2026-09-21T10:00:00", now)).toBe("7 ngày trước");
    expect(groupLabel("2026-08-01T10:00:00", now)).toBe("Cũ hơn");
  });
});

describe("HistoryPanel", () => {
  it("marks the active session and opens another one", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [
        { id: 2, title: "Doanh thu?", turn_count: 3, created_at: "", last_at: new Date().toISOString() },
        { id: 1, title: "Kho?", turn_count: 1, created_at: "", last_at: new Date().toISOString() },
      ],
      total: 2, page: 1, size: 50,
    });
    const onSelect = vi.fn();
    render(<HistoryPanel activeId={2} refreshKey={0} onSelect={onSelect} onNew={vi.fn()} />);
    expect(await screen.findByRole("button", { name: /Doanh thu\?/ })).toHaveAttribute("aria-current", "true");
    fireEvent.click(screen.getByRole("button", { name: /Kho\?/ }));
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});
```

`assistant-screen.test.tsx`:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

let search = "";
const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace }),
  usePathname: () => "/assistant",
  useSearchParams: () => new URLSearchParams(search),
}));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { ApiError, apiFetch } from "@/lib/api-client";
import { saveSession } from "@/lib/session";
import { AssistantScreen } from "./assistant-screen";

const fetchMock = apiFetch as unknown as ReturnType<typeof vi.fn>;
const reply = { answer: "a", headline: "Có 2 đơn.", highlights: [], follow_ups: [], scope_note: null,
  columns: [], kind: "answer", data: [], chart: null, detail: null, session_id: 9 };

describe("AssistantScreen", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    search = "";
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  it("greets, asks a starter question and shows the answer", async () => {
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(path.startsWith("/assistant/sessions") ? { items: [], total: 0, page: 1, size: 50 } : reply),
    );
    render(<AssistantScreen />);
    expect(screen.getByText(/Chào quanly/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Doanh thu 7 ngày gần nhất/ }));
    expect(await screen.findByText("Có 2 đơn.")).toBeInTheDocument();
  });

  it("opens the session named in the URL", async () => {
    search = "session=5";
    fetchMock.mockImplementation((path: string) =>
      Promise.resolve(
        path === "/assistant/sessions/5"
          ? { id: 5, title: "Cũ?", turns: [{ id: 1, question: "Cũ?", headline: "Đáp cũ.", highlights: [], status: "Thành công", occurred_at: "" }] }
          : { items: [], total: 0, page: 1, size: 50 },
      ),
    );
    render(<AssistantScreen />);
    expect(await screen.findByText("Đáp cũ.")).toBeInTheDocument();
  });

  it("falls back to a new chat when the URL session is not the user's", async () => {
    search = "session=99";
    fetchMock.mockImplementation((path: string) =>
      path === "/assistant/sessions/99"
        ? Promise.reject(new ApiError(404, "NOT_FOUND", "Không tìm thấy cuộc trò chuyện."))
        : Promise.resolve({ items: [], total: 0, page: 1, size: 50 }),
    );
    render(<AssistantScreen />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Không tìm thấy cuộc trò chuyện.");
    expect(screen.getByText(/Chào quanly/)).toBeInTheDocument();
    expect(replace).toHaveBeenCalledWith("/assistant");
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd apps/web && pnpm vitest run src/features/assistant` → FAIL.

- [ ] **Step 3: Create `history-panel.tsx`**

```tsx
"use client";

import { Plus } from "lucide-react";
import { useCallback } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch } from "@/lib/api-client";
import { useResource } from "@/lib/use-resource";
import { cn } from "@/lib/utils";
import type { SessionSummary } from "@/types/api";

const GROUPS = ["Hôm nay", "Hôm qua", "7 ngày trước", "Cũ hơn"] as const;

function startOfDay(d: Date): number {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

export function groupLabel(iso: string, now: Date): (typeof GROUPS)[number] {
  const days = Math.round((startOfDay(now) - startOfDay(new Date(iso))) / 86_400_000);
  if (days <= 0) return "Hôm nay";
  if (days === 1) return "Hôm qua";
  if (days <= 7) return "7 ngày trước";
  return "Cũ hơn";
}

function timeOf(iso: string, group: string): string {
  const d = new Date(iso);
  return group === "Hôm nay" || group === "Hôm qua"
    ? d.toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })
    : d.toLocaleDateString("vi-VN", { day: "2-digit", month: "2-digit" });
}

export function HistoryPanel({ activeId, refreshKey, onSelect, onNew }: {
  activeId: number | null;
  refreshKey: number;
  onSelect: (id: number) => void;
  onNew: () => void;
}) {
  const fetcher = useCallback(
    () => apiFetch<{ items: SessionSummary[] }>(`/assistant/sessions?size=50&v=${refreshKey}`),
    [refreshKey],
  );
  const history = useResource(fetcher);
  const now = new Date();

  return (
    <div className="flex h-full min-h-0 flex-col bg-surface">
      <div className="grid gap-2.5 border-b border-border p-3.5">
        <h2 className="text-[15px] font-bold">Trợ lý AI</h2>
        <Button onClick={onNew}><Plus />Cuộc trò chuyện mới</Button>
      </div>
      <nav aria-label="Lịch sử trò chuyện" className="min-h-0 flex-1 overflow-y-auto p-2">
        {history.status === "loading" && (
          <div className="grid gap-2 p-2"><Skeleton className="h-9" /><Skeleton className="h-9" /></div>
        )}
        {history.status === "error" && <p className="p-2 text-danger-fg">{history.message}</p>}
        {history.status === "ready" && history.data.items.length === 0 && (
          <p className="p-2 text-muted">Chưa có cuộc trò chuyện nào.</p>
        )}
        {history.status === "ready" &&
          GROUPS.map((group) => {
            const items = history.data.items.filter((s) => groupLabel(s.last_at, now) === group);
            if (items.length === 0) return null;
            return (
              <div key={group}>
                <p className="px-2 pt-3 pb-1 text-[11px] font-bold tracking-wider text-subtle uppercase">{group}</p>
                {items.map((s) => (
                  <button
                    key={s.id}
                    type="button"
                    aria-current={s.id === activeId ? "true" : undefined}
                    onClick={() => onSelect(s.id)}
                    className={cn(
                      "grid w-full gap-0.5 rounded-control px-2.5 py-2 text-left hover:bg-surface-sunken",
                      s.id === activeId && "bg-primary-subtle hover:bg-primary-subtle",
                    )}
                  >
                    <span className="truncate font-semibold">{s.title}</span>
                    <span className="text-xs text-subtle">{s.turn_count} câu hỏi · {timeOf(s.last_at, group)}</span>
                  </button>
                ))}
              </div>
            );
          })}
      </nav>
    </div>
  );
}
```

The active row changes only its background (user decision, spec §4.2).

- [ ] **Step 4: Create `welcome.tsx`**

```tsx
import { roleLabel } from "@/lib/roles";

import { suggestionsFor } from "./suggestions";

export function Welcome({ username, role, onAsk, composer }: {
  username: string | undefined;
  role: string | undefined;
  onAsk: (text: string) => void;
  composer: React.ReactNode;
}) {
  return (
    <div className="mx-auto grid w-full max-w-3xl gap-5 px-5 pt-16 pb-5 max-sm:pt-8">
      <div className="grid gap-2">
        <h2 className="text-3xl leading-[38px] font-bold tracking-tight text-balance">
          Chào {username ?? "bạn"}, hôm nay bạn muốn xem số liệu gì?
        </h2>
        <p className="text-[15px] text-muted">
          Hỏi bằng tiếng Việt về doanh thu, order, món bán chạy hay tồn kho. Trợ lý chỉ đọc dữ liệu trong phạm vi
          vai trò {role ? roleLabel(role) : "của bạn"}.
        </p>
      </div>
      {composer}
      <div className="grid gap-2 sm:grid-cols-2">
        {suggestionsFor(role).slice(0, 4).map((s) => (
          <button key={s.text} type="button" onClick={() => onAsk(s.text)}
            className="grid gap-1.5 rounded-container border border-border bg-surface px-3.5 py-3 text-left hover:border-ink hover:shadow-lift">
            <span className="text-[11px] font-bold tracking-wider text-subtle uppercase">{s.topic}</span>
            <span className="text-[14.5px] font-semibold">{s.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 5: Create `assistant-screen.tsx`**

```tsx
"use client";

import { PanelLeft, ShieldCheck, X } from "lucide-react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/button";
import { ApiError, apiFetch } from "@/lib/api-client";
import { roleLabel } from "@/lib/roles";
import { parseSession, serverSessionSnapshot, sessionSnapshot, subscribeSession } from "@/lib/session";
import type { SessionDetail } from "@/types/api";

import { AssistantMessage } from "./assistant-message";
import { Composer } from "./composer";
import { HistoryPanel } from "./history-panel";
import { useConversation } from "./use-conversation";
import { Welcome } from "./welcome";

export function AssistantScreen() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const stored = useSyncExternalStore(subscribeSession, sessionSnapshot, serverSessionSnapshot);
  const user = useMemo(() => parseSession(stored), [stored]);
  const [refreshKey, setRefreshKey] = useState(0);
  const [drawer, setDrawer] = useState(false);
  const [openError, setOpenError] = useState<string | null>(null);
  const conversation = useConversation({ onSessionCreated: () => setRefreshKey((k) => k + 1) });
  const bottom = useRef<HTMLDivElement>(null);
  const { turns, pending, ask, reset, load, sessionId } = conversation;

  async function open(id: number) {
    setOpenError(null);
    setDrawer(false);
    try {
      load(await apiFetch<SessionDetail>(`/assistant/sessions/${id}`));
    } catch (error: unknown) {
      reset();
      setOpenError(error instanceof ApiError ? error.message : "Không mở được cuộc trò chuyện.");
      router.replace(pathname);
    }
  }

  const requested = Number(params.get("session"));
  useEffect(() => {
    if (Number.isInteger(requested) && requested > 0) void open(requested);
    // Only the URL value matters; `open` is recreated every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requested]);

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ block: "end" });
  }, [turns]);

  function startNew() {
    reset();
    setOpenError(null);
    setDrawer(false);
    router.replace(pathname);
  }

  const title = turns[0]?.question ?? "Cuộc trò chuyện mới";
  const scope = user ? `${roleLabel(user.role)} · chỉ đọc` : "Chỉ đọc";
  const history = (
    <HistoryPanel activeId={sessionId} refreshKey={refreshKey} onSelect={(id) => void open(id)} onNew={startNew} />
  );

  return (
    <div className="flex h-[calc(100dvh-5.5rem)] overflow-hidden rounded-container border border-border bg-canvas lg:h-[calc(100dvh-3rem)]">
      <aside className="hidden w-72 shrink-0 border-r border-border xl:block">{history}</aside>
      {drawer && (
        <div className="fixed inset-0 z-40 xl:hidden">
          <button aria-label="Đóng lịch sử" className="absolute inset-0 bg-ink/40" onClick={() => setDrawer(false)} />
          <aside className="relative h-full w-72 border-r border-border">
            <button aria-label="Đóng lịch sử" onClick={() => setDrawer(false)}
              className="absolute top-3.5 right-3 z-10 rounded-control p-1 text-subtle hover:bg-surface-sunken">
              <X className="size-4" />
            </button>
            {history}
          </aside>
        </div>
      )}

      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-border bg-surface px-4 py-2.5">
          <Button variant="ghost" size="icon" className="xl:hidden" aria-label="Mở lịch sử" onClick={() => setDrawer(true)}>
            <PanelLeft />
          </Button>
          <h1 className="min-w-0 flex-1 truncate text-base font-bold">{title}</h1>
          <span className="inline-flex h-[26px] items-center gap-1.5 rounded-badge bg-surface-sunken px-2 text-xs font-semibold whitespace-nowrap text-muted ring-1 ring-border ring-inset">
            <ShieldCheck className="size-3.5" aria-hidden />
            {scope}
          </span>
        </header>

        {openError && (
          <p role="alert" className="mx-4 mt-3 rounded-container bg-danger-subtle px-3.5 py-2.5 text-danger-fg shadow-[inset_4px_0_0_0_var(--color-danger)]">
            {openError}
          </p>
        )}

        <div className="min-h-0 flex-1 overflow-y-auto">
          {turns.length === 0 ? (
            <Welcome username={user?.username} role={user?.role} onAsk={(q) => void ask(q)}
              composer={<Composer size="lg" autoFocus disabled={pending} placeholder="Ví dụ: Doanh thu tháng 8 theo từng ngày?" onSubmit={(q) => void ask(q)} />} />
          ) : (
            <div className="mx-auto grid max-w-3xl gap-7 px-5 pt-6 pb-3">
              {turns.map((turn) => (
                <AssistantMessage key={turn.id} turn={turn} onAsk={(q) => void ask(q)} />
              ))}
              <div ref={bottom} />
            </div>
          )}
        </div>

        {turns.length > 0 && (
          <div className="px-5 pt-2 pb-3.5">
            <div className="mx-auto max-w-3xl">
              <Composer size="lg" disabled={pending} placeholder="Hỏi tiếp về số liệu…" onSubmit={(q) => void ask(q)} />
              <p className="mt-2 text-center text-xs text-subtle">
                Trợ lý có thể hiểu sai câu hỏi. Kiểm tra lại số liệu quan trọng ở mục Báo cáo.
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
```

Remove the `eslint-disable-next-line` if lint does not flag the dependency list; if it does and the project forbids disables, wrap `open` in `useCallback` with `[load, reset, router, pathname]` and list it in the effect dependencies instead.

- [ ] **Step 6: Update the page**

```tsx
import { Suspense } from "react";

import { LoadingState } from "@/components/page-states";
import { AssistantScreen } from "@/features/assistant/assistant-screen";

export default function AssistantPage() {
  return (
    <Suspense fallback={<LoadingState rows={4} />}>
      <AssistantScreen />
    </Suspense>
  );
}
```

- [ ] **Step 7: Retire `chat-panel`** — read `chat-panel.test.tsx`, move its `describe("ChartView", …)` block into a new `chart-view.test.tsx` (same imports minus `ChatPanel`), then `git rm apps/web/src/features/assistant/chat-panel.tsx apps/web/src/features/assistant/chat-panel.test.tsx` and confirm `grep -rn "chat-panel" apps/web/src` is empty.

- [ ] **Step 8: Run, lint, type-check, build, commit**

```bash
cd apps/web && pnpm vitest run && pnpm lint && pnpm typecheck && pnpm build
git add -A apps/web/src/features/assistant "apps/web/src/app/(app)/assistant/page.tsx"
git commit -m "feat(assistant): add history, a welcome screen and a full-height chat layout"
```

### Task E4: Floating assistant widget

**Files:**
- Create: `apps/web/src/features/assistant/assistant-widget.tsx`
- Modify: `apps/web/src/components/app-shell.tsx` (mount widget), `apps/web/src/app/layout.tsx` (`Toaster` offset)
- Test: `apps/web/src/features/assistant/assistant-widget.test.tsx` (create)

**Interfaces:**
- Consumes: E2 hook/components, E1 `suggestionsFor`, `MODULE_LIST` from `lib/modules`.
- Produces: `AssistantWidget()` (no props; reads pathname and session).

- [ ] **Step 1: Write the failing test**

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

let pathname = "/inventory";
const push = vi.fn();
vi.mock("next/navigation", () => ({ usePathname: () => pathname, useRouter: () => ({ push }) }));
vi.mock("@/lib/api-client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api-client")>();
  return { ...actual, apiFetch: vi.fn() };
});
import { apiFetch } from "@/lib/api-client";
import { saveSession } from "@/lib/session";
import { AssistantWidget } from "./assistant-widget";

const reply = { answer: "a", headline: "Có 3 nguyên liệu sắp hết.", highlights: [], follow_ups: [],
  scope_note: null, columns: [], kind: "answer", data: [], chart: null, detail: null, session_id: 12 };

describe("AssistantWidget", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    pathname = "/inventory";
    saveSession({ token: "t", role: "MANAGER", username: "quanly" });
  });

  it("is hidden on the assistant and sales screens", () => {
    pathname = "/sales";
    const { rerender } = render(<AssistantWidget />);
    expect(screen.queryByRole("button", { name: /Hỏi trợ lý/ })).not.toBeInTheDocument();
    pathname = "/assistant";
    rerender(<AssistantWidget />);
    expect(screen.queryByRole("button", { name: /Hỏi trợ lý/ })).not.toBeInTheDocument();
  });

  it("opens with Ctrl+K, suggests questions for the current module and closes with Escape", () => {
    render(<AssistantWidget />);
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog", { name: "Trợ lý AI" })).toBeInTheDocument();
    expect(screen.getByText(/Đang ở màn Kho/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /dưới mức tối thiểu/ })).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("keeps the conversation across screens and opens it full-screen", async () => {
    (apiFetch as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(reply);
    const { rerender } = render(<AssistantWidget />);
    fireEvent.click(screen.getByRole("button", { name: /Hỏi trợ lý/ }));
    fireEvent.click(screen.getByRole("button", { name: /dưới mức tối thiểu/ }));
    expect(await screen.findByText("Có 3 nguyên liệu sắp hết.")).toBeInTheDocument();

    pathname = "/reports";
    rerender(<AssistantWidget />);
    expect(screen.getByText("Có 3 nguyên liệu sắp hết.")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Mở toàn màn hình" }));
    expect(push).toHaveBeenCalledWith("/assistant?session=12");
  });
});
```

- [ ] **Step 2: Run to verify failure** — `cd apps/web && pnpm vitest run src/features/assistant/assistant-widget.test.tsx` → FAIL.

- [ ] **Step 3: Create `assistant-widget.tsx`**

```tsx
"use client";

import { Maximize2, MessageSquareText, Minus, Plus } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";

import { Button } from "@/components/ui/button";
import { MODULE_LIST } from "@/lib/modules";
import { roleLabel } from "@/lib/roles";
import { parseSession, serverSessionSnapshot, sessionSnapshot, subscribeSession } from "@/lib/session";

import { AssistantMessage } from "./assistant-message";
import { Composer } from "./composer";
import { suggestionsFor } from "./suggestions";
import { useConversation } from "./use-conversation";

// The POS keeps its pay and send buttons in the bottom-right corner; the full assistant
// page already is the assistant.
const HIDDEN_ON = ["/assistant", "/sales"];

export function AssistantWidget() {
  const pathname = usePathname();
  const router = useRouter();
  const stored = useSyncExternalStore(subscribeSession, sessionSnapshot, serverSessionSnapshot);
  const user = useMemo(() => parseSession(stored), [stored]);
  const [open, setOpen] = useState(false);
  const { turns, pending, ask, reset, sessionId } = useConversation();
  const bottom = useRef<HTMLDivElement>(null);

  const hidden = HIDDEN_ON.some((p) => pathname.startsWith(p));
  const assistantModule = MODULE_LIST.find((m) => m.key === "assistant");
  const allowed = user !== null && (assistantModule?.allowedRoles.includes(user.role) ?? false);
  const current = MODULE_LIST.find((m) => pathname.startsWith(m.path));

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen((value) => !value);
      } else if (event.key === "Escape") {
        setOpen(false);
      }
    }
    if (hidden || !allowed) return;
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [hidden, allowed]);

  useEffect(() => {
    bottom.current?.scrollIntoView?.({ block: "end" });
  }, [turns]);

  if (hidden || !allowed) return null;

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed right-5 bottom-5 z-40 inline-flex h-12 items-center gap-2.5 rounded-overlay bg-ink pr-4.5 pl-3.5 font-bold text-white shadow-float hover:bg-primary-hover"
      >
        <MessageSquareText className="size-4" aria-hidden />
        Hỏi trợ lý
        <kbd className="rounded-badge bg-white/15 px-1.5 font-mono text-[11px] font-medium text-white/80">Ctrl K</kbd>
      </button>
    );
  }

  return (
    <section
      role="dialog"
      aria-label="Trợ lý AI"
      className="fixed right-5 bottom-5 z-40 flex h-[min(600px,calc(100dvh-2.5rem))] w-[min(420px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-overlay border border-border-strong bg-surface shadow-float max-sm:inset-0 max-sm:h-auto max-sm:w-auto max-sm:rounded-none"
    >
      <header className="flex items-center gap-1.5 border-b border-border py-2 pr-2 pl-3.5">
        <h2 className="flex-1 text-[15px] font-bold">Trợ lý AI</h2>
        <span className="rounded-badge bg-surface-sunken px-2 py-0.5 text-xs font-semibold text-muted ring-1 ring-border ring-inset">
          {roleLabel(user.role)}
        </span>
        <Button variant="ghost" size="icon" aria-label="Cuộc trò chuyện mới" onClick={reset}><Plus /></Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Mở toàn màn hình"
          onClick={() => {
            setOpen(false);
            router.push(sessionId ? `/assistant?session=${sessionId}` : "/assistant");
          }}
        >
          <Maximize2 />
        </Button>
        <Button variant="ghost" size="icon" aria-label="Thu nhỏ" onClick={() => setOpen(false)}><Minus /></Button>
      </header>

      <div className="min-h-0 flex-1 overflow-y-auto bg-canvas p-3.5">
        {turns.length === 0 ? (
          <div className="grid gap-2.5">
            {current && <p className="text-xs text-subtle">Đang ở màn {current.title} · câu hỏi gợi ý theo màn này</p>}
            {suggestionsFor(user.role, current?.key).slice(0, 3).map((s) => (
              <button key={s.text} type="button" onClick={() => void ask(s.text)}
                className="rounded-control border border-border bg-surface px-3 py-2.5 text-left font-medium hover:border-ink">
                {s.text}
              </button>
            ))}
          </div>
        ) : (
          <div className="grid gap-5">
            {turns.map((turn) => (
              <AssistantMessage key={turn.id} turn={turn} compact onAsk={(q) => void ask(q)} />
            ))}
            <div ref={bottom} />
          </div>
        )}
      </div>

      <div className="border-t border-border p-2.5">
        <Composer size="sm" autoFocus disabled={pending} placeholder="Hỏi nhanh về số liệu…" onSubmit={(q) => void ask(q)} />
      </div>
    </section>
  );
}
```

The widget stays mounted inside `AppShell` across route changes, so `useConversation` state survives navigation (spec §4.3). `user` is non-null past the `allowed` guard; if TypeScript does not narrow it, read `const role = user?.role ?? ""` before the guards and use `role`.

- [ ] **Step 4: Mount it and move toasts** — in `app-shell.tsx` import `AssistantWidget` and render `<AssistantWidget />` right after `<ChangePasswordDialog … />`; in `app/layout.tsx` change the `Toaster` to `<Toaster position="bottom-right" richColors closeButton offset={{ bottom: 88, right: 20 }} />` (sonner 2 accepts an offset object; if the type rejects it, use `offset={88}` and note that it also moves the side offset).

- [ ] **Step 5: Run everything, commit**

```bash
cd apps/web && pnpm vitest run && pnpm lint && pnpm typecheck && pnpm build
git add apps/web/src/features/assistant/assistant-widget.tsx apps/web/src/features/assistant/assistant-widget.test.tsx apps/web/src/components/app-shell.tsx apps/web/src/app/layout.tsx
git commit -m "feat(assistant): add a floating assistant widget outside the POS"
```

---

## Phase F — Docs and verification

### Task F1: Report and design docs

**Files:**
- Modify: `docs/BaoCao_HeThongQuanLyNhaHang.md` (§1.4.3, FR-SALE summary row ~1837, limitation 6 ~1954, and every mention of "chữ ký webhook" for the QR gateway)
- Modify: `docs/design/tokens.md` (§6 components list: add `SalesStepper`, assistant components; widget position note)

- [ ] **Step 1: Find every place to change**

Run: `grep -n "cổng thanh toán QR thật\|ngoài phạm vi\|bộ giả lập\|chữ ký webhook\|chuyển khoản thủ công" docs/BaoCao_HeThongQuanLyNhaHang.md`

- [ ] **Step 2: Edit the report** — for each hit that describes the QR gateway, replace the out-of-scope wording with: "Thanh toán QR dùng VietQR chuyển khoản qua cổng SePay (môi trường Test mode) thông qua một adapter; xác nhận bằng webhook có API key và API tra cứu giao dịch. Bộ giả lập có chữ ký HMAC được giữ cho kiểm thử tự động." Keep the limitation list numbered; limitation 6 becomes: "Không tích hợp thanh toán thẻ ngân hàng; QR ở trạng thái 'Chờ xác nhận thanh toán' cho đến khi webhook SePay xác nhận hoặc hết 10 phút thì chuyển 'Chờ đối soát'." Keep MySQL, `Images/` paths and all other sections untouched.

- [ ] **Step 3: Update `tokens.md` §6** — add to the shared components paragraph: "Bán hàng: `SalesStepper` (3 bước, mục hiện tại nền `surface-sunken`, số bước nền `primary`). Trợ lý: `AssistantMessage`, `Composer`, `ResultTabs`, `HistoryPanel` (mục đang mở chỉ đổi nền `primary-subtle`, không viền), `AssistantWidget` (góc dưới phải, ẩn ở `/sales` và `/assistant`; toast dời lên 88px)."

- [ ] **Step 4: Commit**

```bash
git add docs/BaoCao_HeThongQuanLyNhaHang.md docs/design/tokens.md
git commit -m "docs: describe the SePay QR flow and the new sales and assistant components"
```

### Task F2: Full gate and live checks

- [ ] **Step 1: Run the gate** — `make gate` at the repo root. Expected: format, lint, typecheck, tests, build all green. Report any unfinished check separately.

- [ ] **Step 2: Live check of the sales flow** (local DB, simulator gateway) — run API + web, log in as `seed_cashier`, then: open a free table → add two priced dishes → "Gửi bếp" → back on the floor the table shows the running total → "Thanh toán" → cash 500.000 ₫ shows the right change → done step shows the invoice. Take one screenshot per step.

- [ ] **Step 3: SePay spike (spec §10 risk)** — with the user's SePay Test-mode credentials in `.env` and a cloudflared tunnel URL configured as the webhook: create a QR, run "Giả lập giao dịch" in SePay with the shown amount and content, confirm the order settles. Then call `POST /sales/payments/{id}/check` on a fresh QR with only `SEPAY_API_TOKEN` (no tunnel) and record whether the Test-mode listing API returns the simulated transfer. Report the result; if it does not, note in the report that "Kiểm tra lại" relies on the webhook in Test mode.

- [ ] **Step 4: Live check of the assistant** — log in as `seed_manager`: ask a starter question, open the "SQL" and "Bảng" tabs, click a follow-up, open an old session from history, open `/assistant?session=<another user's id>` and confirm the error + new chat, open the widget with Ctrl+K on `/inventory`, navigate to `/reports` and confirm the conversation is still there.

- [ ] **Step 5: Hand back** — summarise results (gate, screenshots, SePay spike outcome) and leave commits for the user to review.
