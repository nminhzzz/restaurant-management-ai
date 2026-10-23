"""Read-only inventory, reservation and idempotence evidence."""

import argparse
import asyncio
import hashlib
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.modules.catalog.models import DiningTable, Dish, Ingredient, Supplier
from app.modules.inventory.models import IngredientLot, StockMovement
from app.modules.inventory.stock import available_quantity
from app.modules.sales.models import Invoice, Order, Reservation, ReservationDetail
from app.shared import business_date


def amount(value):
    return format(Decimal(value or 0).quantize(Decimal(".0001")), "f")


async def snapshot(session):
    counts = {}
    for name, model in (
        ("orders", Order),
        ("dishes", Dish),
        ("ingredients", Ingredient),
        ("tables", DiningTable),
        ("suppliers", Supplier),
        ("movements", StockMovement),
        ("lots", IngredientLot),
    ):
        counts[name] = await session.scalar(select(func.count()).select_from(model))
    statuses = dict(
        (await session.execute(select(Order.status, func.count()).group_by(Order.status))).all()
    )
    lots = [
        {
            "id": row.id,
            "ingredient_id": row.ingredient_id,
            "remaining": amount(row.quantity_remaining),
        }
        for row in (await session.scalars(select(IngredientLot).order_by(IngredientLot.id))).all()
    ]
    ledger = [
        {
            "id": row.id,
            "lot_id": row.lot_id,
            "kind": row.kind,
            "qty": amount(row.qty),
            "order_line_id": row.order_line_id,
            "receipt_line_id": row.receipt_line_id,
        }
        for row in (await session.scalars(select(StockMovement).order_by(StockMovement.id))).all()
    ]
    revenue = defaultdict(Decimal)
    invoices = (await session.execute(select(Invoice.business_date, Invoice.total))).all()
    for day, total in invoices:
        revenue[day.isoformat()] += total
    report_totals = {
        day: {
            "revenue_day": amount(total),
            "revenue_month": amount(
                sum(value for key, value in revenue.items() if key[:7] == day[:7])
            ),
        }
        for day, total in sorted(revenue.items())
    }
    result = {
        "counts": counts,
        "statuses": statuses,
        "lots": lots,
        "ledger": ledger,
        "total_revenue": amount(sum(revenue.values())),
        "report_totals": report_totals,
    }
    result["checksum"] = hashlib.sha256(
        json.dumps(result, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return result


async def verify(session):
    failures = []
    lots = (await session.scalars(select(IngredientLot))).all()
    ledger_by_lot = dict(
        (
            await session.execute(
                select(StockMovement.lot_id, func.sum(StockMovement.qty)).group_by(
                    StockMovement.lot_id
                )
            )
        ).all()
    )
    lots_by_ingredient = defaultdict(Decimal)
    for lot in lots:
        lots_by_ingredient[lot.ingredient_id] += lot.quantity_remaining
        if lot.quantity_remaining < 0 or amount(lot.quantity_remaining) != amount(
            ledger_by_lot.get(lot.id, 0)
        ):
            failures.append(f"lot_ledger:{lot.id}")
    ledger_by_ingredient = dict(
        (
            await session.execute(
                select(StockMovement.ingredient_id, func.sum(StockMovement.qty)).group_by(
                    StockMovement.ingredient_id
                )
            )
        ).all()
    )
    now = business_date.now().replace(tzinfo=None)
    today = business_date.business_date_of(now)
    held = dict(
        (
            await session.execute(
                select(ReservationDetail.lot_id, func.sum(ReservationDetail.quantity))
                .join(Reservation, Reservation.id == ReservationDetail.reservation_id)
                .where(Reservation.status == "Đang giữ", Reservation.expires_at > now)
                .group_by(ReservationDetail.lot_id)
            )
        ).all()
    )
    eligible = defaultdict(Decimal)
    for lot in lots:
        if lot.status != "Hết hạn" and (lot.expiry_date is None or lot.expiry_date >= today):
            eligible[lot.ingredient_id] += lot.quantity_remaining - held.get(lot.id, 0)
        if held.get(lot.id, 0) > lot.quantity_remaining:
            failures.append(f"overbooked_lot:{lot.id}")
    for ingredient in (await session.scalars(select(Ingredient))).all():
        totals = [
            amount(value)
            for value in (
                ingredient.stock_qty,
                lots_by_ingredient[ingredient.id],
                ledger_by_ingredient.get(ingredient.id, 0),
            )
        ]
        if ingredient.stock_qty < 0 or len(set(totals)) != 1:
            failures.append(f"ingredient_ledger:{ingredient.id}")
        if amount(await available_quantity(session, ingredient.id)) != amount(
            eligible[ingredient.id]
        ):
            failures.append(f"active_hold_availability:{ingredient.id}")
    # A consumed line may span FIFO lots; it must never debit the same lot twice.
    duplicates = (
        await session.execute(
            select(StockMovement.order_line_id, StockMovement.lot_id)
            .where(StockMovement.kind == "Trừ tự động")
            .group_by(StockMovement.order_line_id, StockMovement.lot_id)
            .having(func.count() > 1)
        )
    ).all()
    failures.extend(f"duplicate_consumption:{line}:{lot}" for line, lot in duplicates)
    for model, column, label in (
        (Order, Order.request_id, "duplicate_send"),
        (Reservation, Reservation.order_line_id, "duplicate_hold_send"),
    ):
        duplicates = (
            await session.execute(
                select(column).where(column.is_not(None)).group_by(column).having(func.count() > 1)
            )
        ).all()
        failures.extend(f"{label}:{row[0]}" for row in duplicates)
    return failures


async def run(args):
    from scripts.perf.seed import dedicated_database

    dedicated_database(args.database_url)
    engine = create_async_engine(args.database_url)
    try:
        async with async_sessionmaker(engine, expire_on_commit=False)() as session:
            schedule = await business_date.load_business_date_schedule(session)
            with business_date.business_date_schedule(schedule):
                failures = await verify(session)
                current = await snapshot(session)
            if args.baseline:
                baseline = json.loads(Path(args.baseline).read_text())
                # Loads intentionally add movements: compare unchanged historical invoice revenue,
                # while reconciling the complete current ledger independently above.
                if current["total_revenue"] != baseline["total_revenue"]:
                    failures.append("historical_revenue_changed")
            Path(args.output).write_text(
                json.dumps(
                    {"failures": failures, "snapshot": current}, indent=2, ensure_ascii=False
                )
            )
            return int(bool(failures))
    finally:
        await engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Kiểm tra bất biến Phụ lục J, chỉ đọc CSDL thử.")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--baseline")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args)))
