"""Stored lot status (document 04 F.21, BR-LOT-01).

The status is saved on the lot and refreshed in the same transaction as every stock change.
"Đã hủy" is final (the source receipt was cancelled). Otherwise, in this order: nothing left ->
"Đã dùng hết"; past its expiry -> "Hết hạn"; inside the warning window -> "Sắp hết hạn"; else
"Còn hạn". A lot without an expiry date is never "Hết hạn" or "Sắp hết hạn".
"""

import asyncio
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.modules.inventory.models import IngredientLot
from app.modules.settings.models import SystemConfig
from app.shared import business_date
from app.shared.enums import LotStatus

DEFAULT_WARNING_DAYS = 3


def derive_lot_status(lot: IngredientLot, today: date, warning_days: int) -> str:
    if lot.status == LotStatus.DA_HUY.value:
        return LotStatus.DA_HUY.value
    if Decimal(str(lot.quantity_remaining)) <= 0:
        return LotStatus.DA_DUNG_HET.value
    if lot.expiry_date is not None:
        if lot.expiry_date < today:
            return LotStatus.HET_HAN.value
        if lot.expiry_date <= today + timedelta(days=warning_days):
            return LotStatus.SAP_HET_HAN.value
    return LotStatus.CON_HAN.value


async def sync_lot_status(session: AsyncSession, lot: IngredientLot) -> None:
    warning = await session.scalar(select(SystemConfig.expiry_warning_days).limit(1))
    today = business_date.business_date_of(business_date.now())
    lot.status = derive_lot_status(lot, today, DEFAULT_WARNING_DAYS if warning is None else warning)


async def refresh_all_lot_statuses(session: AsyncSession) -> int:
    """Re-derive every lot status; returns how many lots changed.

    Time alone moves a lot to "Sắp hết hạn" or "Hết hạn", with no stock transaction to trigger
    `sync_lot_status`, so this runs on a schedule and once after the rule was introduced.
    """
    warning = await session.scalar(select(SystemConfig.expiry_warning_days).limit(1))
    days = DEFAULT_WARNING_DAYS if warning is None else warning
    schedule = await business_date.load_business_date_schedule(session)
    with business_date.business_date_schedule(schedule):
        today = business_date.business_date_of(business_date.now())
    rows = (
        await session.execute(
            select(
                IngredientLot.id,
                IngredientLot.status,
                IngredientLot.quantity_remaining,
                IngredientLot.expiry_date,
            ).where(IngredientLot.status != LotStatus.DA_HUY.value)
        )
    ).all()
    changes: dict[str, list[int]] = defaultdict(list)
    for lot_id, status, remaining, expiry in rows:
        probe = IngredientLot(status=status, quantity_remaining=remaining, expiry_date=expiry)
        wanted = derive_lot_status(probe, today, days)
        if wanted != status:
            changes[wanted].append(lot_id)
    for status, ids in changes.items():
        for start in range(0, len(ids), 500):
            await session.execute(
                update(IngredientLot)
                .where(IngredientLot.id.in_(ids[start : start + 500]))
                .values(status=status)
            )
    return sum(len(ids) for ids in changes.values())


async def lot_status_tick(*, factory: async_sessionmaker[AsyncSession] | None = None) -> int:
    if factory is None:
        from app.core.database import get_session_factory

        factory = get_session_factory()
    async with factory() as session:
        try:
            changed = await refresh_all_lot_statuses(session)
            await session.commit()
            return changed
        except Exception:
            await session.rollback()
            raise


if __name__ == "__main__":
    print(f"{asyncio.run(lot_status_tick())} lot status(es) updated")
