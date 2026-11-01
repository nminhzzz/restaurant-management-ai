"""Stored lot status (document 04 F.21, BR-LOT-01).

The status is saved on the lot and refreshed in the same transaction as every stock change.
"Đã hủy" is final (the source receipt was cancelled). Otherwise, in this order: nothing left ->
"Đã dùng hết"; past its expiry -> "Hết hạn"; inside the warning window -> "Sắp hết hạn"; else
"Còn hạn". A lot without an expiry date is never "Hết hạn" or "Sắp hết hạn".
"""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
