"""Declarative base and shared column mixins.

Convention: database identifiers follow the relational schema in the report
(Vietnamese: `NGUYEN_LIEU`, `MaNguyenLieu`), while Python identifiers stay English.
"""

from datetime import date, datetime

from sqlalchemy import BigInteger as _BigInteger
from sqlalchemy import Date, DateTime, MetaData, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}


# MySQL needs BIGINT for all PKs (Long), but SQLite AUTOINCREMENT only works with INTEGER.
# CrossBigInteger compiles to BIGINT on MySQL and INTEGER on SQLite.
class CrossBigInteger(_BigInteger):
    """BIGINT on MySQL, INTEGER on SQLite (for AUTOINCREMENT compat)."""

    pass


@compiles(CrossBigInteger, "sqlite")
def _compile_cross_bigint_sqlite(element, compiler, **kw):  # type: ignore[no-untyped-def]
    return "INTEGER"


# Alias used by models: keep name BigInteger so imports don't change
BigInteger = CrossBigInteger

# Patch sqlalchemy global so `from sqlalchemy import BigInteger` still works for SQLite
import sqlalchemy as _sa  # type: ignore[import-untyped]

_sa.BigInteger = CrossBigInteger  # type: ignore[misc]


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        "NgayTao", DateTime, server_default=func.now(), nullable=False
    )


class SoftDeleteMixin:
    """Soft delete flag shared by every catalogue entity (business rule 20)."""

    is_deleted: Mapped[bool] = mapped_column("DaXoa", default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column("NgayXoa", DateTime, nullable=True)


class BusinessDateMixin:
    """Denormalized BusinessDate for reporting queries (Quy uoc #5)."""

    business_date: Mapped[date] = mapped_column("BusinessDate", Date, nullable=False)
