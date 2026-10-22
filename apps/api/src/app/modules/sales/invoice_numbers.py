"""Transaction-local invoice numbers, serialised per business date."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sales.models import InvoiceCounter


async def next_invoice_number(session: AsyncSession, day: date) -> str:
    dialect = session.get_bind().dialect.name
    if dialect == "mysql":
        statement = mysql_insert(InvoiceCounter).values(business_date=day, count=1)
        await session.execute(statement.on_duplicate_key_update(SoDaCap=InvoiceCounter.count + 1))
    elif dialect == "sqlite":
        statement_sqlite = sqlite_insert(InvoiceCounter).values(business_date=day, count=1)
        await session.execute(
            statement_sqlite.on_conflict_do_update(
                index_elements=[InvoiceCounter.business_date],
                set_={"SoDaCap": InvoiceCounter.count + 1},
            )
        )
    else:
        raise RuntimeError("Invoice numbering requires MySQL")
    # A locking read sees the counter changed by the upsert even when the request
    # established a REPEATABLE READ snapshot before another till committed.
    number = await session.scalar(
        select(InvoiceCounter.count).where(InvoiceCounter.business_date == day).with_for_update()
    )
    return f"HD-{day:%Y%m%d}-{number:04d}"
