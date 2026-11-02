"""Review-only deterministic interleaving of a sweep and receipt cancellation."""
from datetime import timedelta
from decimal import Decimal
import pytest
from sqlalchemy import update,select
from sqlalchemy.sql.dml import Update
from app.modules.catalog.models import Ingredient
from app.modules.inventory.models import IngredientLot
from app.modules.inventory.lot_status import refresh_all_lot_statuses
from app.modules.settings.service import seed_reference_data
from app.shared import business_date

@pytest.mark.anyio
async def test_sweep_preserves_cancellation_after_its_read(session,monkeypatch):
    await seed_reference_data(session)
    ing=Ingredient(name='Review race',unit='g',stock_qty=Decimal(1),min_stock=0)
    session.add(ing)
    await session.flush()
    lot=IngredientLot(ingredient_id=ing.id,received_quantity=Decimal(1),quantity_remaining=Decimal(1),status='Còn hạn',received_at=business_date.now(),expiry_date=business_date.business_date_of(business_date.now())-timedelta(days=1))
    session.add(lot)
    await session.commit()
    lid=lot.id
    original=session.execute
    injected=False
    async def interleave(statement,*args,**kwargs):
        nonlocal injected
        if isinstance(statement,Update) and statement.table.name=='LO_NGUYEN_LIEU' and not injected:
            injected=True
            await original(update(IngredientLot).where(IngredientLot.id==lid).values(status='Đã hủy',quantity_remaining=0))
            await session.commit()
        return await original(statement,*args,**kwargs)
    monkeypatch.setattr(session,'execute',interleave)
    await refresh_all_lot_statuses(session)
    await session.commit()
    status=await session.scalar(select(IngredientLot.status).where(IngredientLot.id==lid))
    assert injected
    assert status=='Đã hủy',f'Sweep overwrote final cancellation with {status!r}'
