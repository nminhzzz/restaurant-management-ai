"""Declarative base and shared column mixins.

Convention: database identifiers follow the ERD in the report (Vietnamese:
`NGUYEN_LIEU`, `MaNguyenLieu`), while Python identifiers stay English.
"""

from datetime import datetime

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s",
    "pk": "pk_%(table_name)s",
}


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
